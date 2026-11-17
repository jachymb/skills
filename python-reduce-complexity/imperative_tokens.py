"""Count the imperative lexical tokens of Python sources.

Usage: python imperative_tokens.py [FILE...]

A file is a Python source or a notebook (``.ipynb``). Of a notebook with a Python kernel, the code cells count;
IPython is imported only then, and says which magics it has built in:

- a line magic or shell line (``%config ...``, ``!pip ...``) counts as the call IPython turns it into;
- a cell under a cell magic (``%%bash``, ``%%html``) counts 0, except under a magic that runs the body as Python
  (the ``ExecutionMagics``, such as ``%%time`` and ``%%capture``): there the magic counts as a line magic and
  the body as code;
- a magic that is not built in, such as one from an extension, counts 0 and a warning is printed.

A notebook with another kernel counts 0. Without a file, the source is read from standard input, as UTF-8: a
way to weigh a snippet.

A token is what `tokenize` yields. Declarative syntax is not counted:

- layout (newlines, indentation) and comments;
- imports and docstrings;
- ``def`` and ``class`` headers, from the first decorator to the colon that opens the body:
  decorators, parameters, default values, base classes and the return annotation;
- variable annotations (``x: int = 1`` counts as ``x = 1``, a bare ``x: int`` as nothing) and ``type`` aliases;
- the name of a keyword argument and its ``=``, so ``f(key=value)`` weighs as much as ``f(value)``;
- attribute qualification: the ``.`` and the name after it, so ``a.b.c.d`` weighs as much as ``d``.

Everything else counts: operators, commas and both brackets of a pair. A call ``f(x)`` therefore weighs one more
than an operator ``a + b``.

Needs Python 3.12 or later, where an f-string is tokenized into its parts. Compare only counts taken with the
same interpreter.
"""

import ast
import io
import json
import re
import sys
import tokenize
from bisect import bisect_left
from collections.abc import Iterable, Iterator
from functools import singledispatch
from pathlib import Path

Position = tuple[int, int]  # (line, column), as in `tokenize`

LAYOUT = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}
# A magic as IPython rewrites it, with its kind and name: a `%name ...` line, or a whole `%%name` cell.
# ponytail: only a magic that is a line of its own; `x = %name ...` counts as the call, unchecked.
MAGIC = re.compile(r"^[ \t]*get_ipython\(\)\.run_(line|cell)_magic\('([^']+)'.*\n?", re.MULTILINE)

SELF_CHECK = '''
"""Docstring."""
import numpy as np

@decorator(option=1)
class A(Base):
    """Docstring."""
    x: int
    y: float = 2.0  # `y = 2.0`: 3 tokens

    def f(self, a: int, b=3) -> float:
        self.total = np.round(a, decimals=b)  # `self = np(a, b)`: 8 tokens
        return self.total  # `return self`: 2 tokens
'''


def start(node: ast.stmt | ast.expr | ast.keyword) -> Position:
    return node.lineno, node.col_offset


def end(node: ast.stmt | ast.expr) -> Position:
    return node.end_lineno or 0, node.end_col_offset or 0


@singledispatch
def declarative_spans(node: ast.AST, starts: list[Position]) -> Iterable[tuple[Position, Position]]:
    """Return the source ranges of `node`, as (start, end) with the end excluded, whose tokens do not count.

    The kinds of node that have any are registered below. `starts` holds the sorted positions of the tokens.
    """
    return ()


@declarative_spans.register
def import_or_alias(node: ast.Import | ast.ImportFrom | ast.TypeAlias,
                    starts: list[Position]) -> Iterator[tuple[Position, Position]]:
    """Yield the whole statement."""
    yield start(node), end(node)


@declarative_spans.register
def annotation(node: ast.AnnAssign, starts: list[Position]) -> Iterator[tuple[Position, Position]]:
    """Yield the annotation, and the target with it when nothing is assigned."""
    yield end(node.target) if node.value else start(node), end(node.annotation)


@declarative_spans.register
def qualification(node: ast.Attribute, starts: list[Position]) -> Iterator[tuple[Position, Position]]:
    """Yield the `.` and the name, not a bracket closing the value."""
    yield starts[bisect_left(starts, end(node)) - 2], end(node)


@declarative_spans.register
def keyword_name(node: ast.keyword, starts: list[Position]) -> Iterator[tuple[Position, Position]]:
    """Yield the name and its `=`, not a bracket opening the value."""
    if node.arg:
        yield start(node), starts[bisect_left(starts, start(node)) + 2]


@declarative_spans.register(ast.Module)
def docstring(node: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
              starts: list[Position]) -> Iterator[tuple[Position, Position]]:
    """Yield the docstring, if there is one."""
    if ast.get_docstring(node) is not None:
        yield start(node.body[0]), end(node.body[0])


@declarative_spans.register
def header(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
           starts: list[Position]) -> Iterator[tuple[Position, Position]]:
    """Yield the header of a definition, from its first decorator to its body, then its docstring."""
    first_line = (node.decorator_list or [node])[0].lineno
    yield (first_line, 0), start(node.body[0])
    yield from docstring(node, starts)


def count(source: str) -> int:
    """Return the number of imperative tokens in `source`."""
    # `ast` counts columns in UTF-8 bytes, `tokenize` in characters: one ASCII letter per character makes
    # them agree without changing a token (non-ASCII is legal only in names, strings and comments; no
    # keyword contains a `z`).
    source = re.sub(r"[^\x00-\x7f]", "z", source)
    starts = [
        token.start for token in tokenize.generate_tokens(io.StringIO(source).readline) if token.type not in LAYOUT
    ]
    uncounted: set[int] = set()
    for node in ast.walk(ast.parse(source)):
        for span_start, span_end in declarative_spans(node, starts):
            uncounted.update(range(bisect_left(starts, span_start), bisect_left(starts, span_end)))
    return len(starts) - len(uncounted)


def read(path: str) -> str:
    """Return the Python source of `path`: its text, or that of the code cells of a notebook."""
    text = Path(path).read_text(encoding="utf-8-sig")
    return notebook_source(json.loads(text), path) if path.endswith(".ipynb") else text


def notebook_source(notebook: dict, path: str) -> str:
    """Return the Python source of the code cells of `notebook`, as IPython runs them.

    A notebook whose kernel is not Python has none. A built-in line magic stays, as the call IPython turns it
    into. A cell under a cell magic is dropped, unless the magic is one of IPython's execution magics
    (``%%time``): those run the cell's body as Python, so the magic becomes a line magic and the body stays
    code. A magic that is not built in is dropped with a warning, which names the notebook by `path`.
    """
    if notebook["metadata"].get("kernelspec", {}).get("language", "python") != "python":
        return ""
    from IPython.core.interactiveshell import InteractiveShell  # only a Python notebook needs IPython
    from IPython.core.magics import ExecutionMagics
    from traitlets.config import Config

    shell = InteractiveShell.instance(config=Config(HistoryManager=Config(enabled=False)))  # no history session
    execution_magics = "|".join(ExecutionMagics.magics["cell"])
    first_percent = re.compile(rf"^\s*%(?=%({execution_magics})\b)")  # without it, the cell magic is a line magic

    def counted(magic: re.Match[str]) -> str:
        kind, name = magic.groups()
        built_in = shell.find_line_magic(name) or shell.find_cell_magic(name)
        if not built_in:
            print(f"warning: {path}: the {kind} magic {name!r} is not built into IPython and counts 0")
        return magic[0] if built_in and kind == "line" else ""

    cells = ("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code")
    sources = (shell.transform_cell(first_percent.sub("", cell)) for cell in cells)
    return MAGIC.sub(counted, "\n".join(sources))


def main(paths: list[str]) -> None:
    """Print the count of every file in `paths` and their total, or the count of standard input without files."""
    if not paths:
        print(count(sys.stdin.buffer.read().decode("utf-8-sig")))
        return
    counts = {path: count(read(path)) for path in paths}
    counts["total"] = sum(counts.values())
    for label, file_count in counts.items():
        print(f"{file_count}\t{label}")


if __name__ == "__main__":
    assert count(SELF_CHECK) == 13, "self-check failed: the counting rules do not hold on this interpreter"
    main(sys.argv[1:])
