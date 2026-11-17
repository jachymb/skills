---
name: python-reduce-complexity
description: Measure and reduce the complexity of Python code, counted as imperative lexical tokens by a bundled script. Proposes simplifications, verifies that each is functionally equivalent and re-measures to confirm the count fell. Use when the user asks to reduce, measure, compare or audit code complexity, to simplify, shrink or slim down Python code, asks whether a change made the code simpler or more complex, mentions "imperative tokens" or a token count, or invokes /python-reduce-complexity. The argument is a Python file or notebook, or a list of them.
argument-hint: "<file.py | notebook.ipynb> [...]"
---

# Reduce Python complexity

Files: `$ARGUMENTS`

Code complexity is preferably kept low. Complexity is measured as the number of Python lexical tokens that are
part of imperative code: syntax that executes something. Declarations organize the code without adding to its
logic, so they are free.

## What counts

`imperative_tokens.py`, next to this file, is the definition.

Not counted:

- `def` and `class` headers, from the first decorator to the colon that opens the body: decorators, parameters,
  default values, base classes, return annotation. All of it is evaluated once, with the definition, and
  declares an interface.
- Type annotations (`x: int = 1` counts as `x = 1`, a bare `x: int` as nothing) and `type` aliases.
- Imports, comments, docstrings, newlines and indentation.
- The name of a keyword argument in a call: `f(key=value)` weighs as much as `f(value)`. Passing an argument
  by keyword is preferred in most situations, so it costs nothing.
- Attribute qualification: `a.b.c.d` weighs as much as `d`. A dotted path names one object. Counting it would
  reward `from numpy import log` over `np.log`, or a local alias for `self.x`, and neither changes any logic.

Counted: every other token. Statements (`if`, `for`, `while`, `try`, `with`, `return`, `raise`, …), assignments,
operators, calls, literals, comprehensions and lambdas, with their commas, colons and both brackets of a pair.
A call therefore weighs one more than the operator that does the same: `a.update(b)` is 4 tokens, `a |= b` is 3.

Of a notebook (`.ipynb`), the code cells count. A magic or shell line (`%config …`, `!pip …`) counts as the
call IPython turns it into. A cell under a cell magic (`%%bash`, `%%html`) counts 0. The exception is a cell
magic that runs the body as Python (IPython's `ExecutionMagics`, such as `%%time` and `%%capture`): the magic
counts as a line magic and the body as code. A magic that is not built into the installed IPython, such as one
from an extension, counts 0 and the script prints a warning: pass that warning on in the report. A notebook
whose kernel is not Python counts 0. The script imports IPython only when it is given a Python notebook, and
asks it which magics are built in.

## The count is a proxy

A lower count is the evidence of a simplification, not the simplification itself.

- **Significant refactors are allowed:** a new helper function, a new base class, a new file. The count is then
  compared over all affected files combined (step 4), so logic moved between files nets to zero.
- **Needs its own justification:** moving logic where the script does not look, which is a default value, a
  decorator argument, a base-class expression or a new dependency. The proposal states why the change is good
  apart from the lower count.
- **Forbidden:** code in a string for `eval` or `exec`.
- **Inlining a variable that is used once** is acceptable only when it does not hurt readability. A good name
  for an intermediate variable helps the reader understand the intent.
- **Not reductions:** removing behavior (validation at a boundary, error handling, a supported case), and
  trading readability for a few tokens (a dense one-liner, a dropped trailing comma).

The project's own rules (`CLAUDE.md`, coding guidelines) outrank the count.

## Steps

1. **Baseline.** Run the script on the files of the argument with the project's interpreter (Python 3.12 or
   later) and keep the output:

   ```
   python "${CLAUDE_SKILL_DIR}/imperative_tokens.py" <file.py | notebook.ipynb> [...]
   ```

   Run the tests now: a suite that fails before the change can verify nothing after it. If the user asked only
   for a measurement, report it and stop.

2. **Propose.** Read the code and look for logic that can go, roughly in order of yield:
   - dead code: unused functions, parameters and branches that cannot be taken;
   - the same logic written twice, here or in another file, which a shared helper or base class would hold once;
   - handwritten code that the standard library, builtin or an installed dependency already provides; standard
     library utilities like `itertools`, `functools` or `operator` may help;
   - loops that build a value: a comprehension is usually better than a loop, and occasionally the `filter`
     or `map` builtin is simpler than a comprehension;
   - method calls that an overloaded operator replaces: `a | b` for `a.union(b)`, `a |= b` for `a.update(b)`,
     `a @ b` for `a.dot(b)`. Check the operand types first: `|=` on a set needs a set, where `.update()` takes
     any iterable;
   - branches that collapse into data (a mapping) or into the general path;
   - state and conversions that exist only to be undone;
   - defensive checks away from a program boundary.

   To weigh a snippet, such as the lines of a proposal before and after, pipe it to the script without a file
   argument. It prints the count alone. The snippet has to parse on its own, so dedent it:

   ```
   python "${CLAUDE_SKILL_DIR}/imperative_tokens.py" <<'EOF'
   uncounted |= set(range(first, last))
   EOF
   ```

   Show each proposal as code shape, the key lines before and after, with the expected saving in tokens, the
   other files it touches and any justification the previous section asks for. Apply on the user's go-ahead, or
   directly if they already asked for the changes to be made.

3. **Apply and verify equivalence**, one proposal at a time, so that a failure points at its cause.
   - Before the first edit to a file outside the baseline, measure it and add it to the baseline. A new file
     starts at 0.
   - The tests pass, unchanged. A test edited together with the code it checks no longer checks it; if one
     must change (it calls a removed helper), say so.
   - Tests that never execute the changed lines prove nothing. For those lines, run the old version
     (`git stash`, or `git show HEAD:<path>` into a scratch file) and the new one on the same inputs, edge
     cases included, and compare the outputs. Floating-point results are identical, or the report states the
     size of the difference.
   - A change in public behavior (a signature, an exception type, the order of an output) is not an equivalent
     change. It needs the user's explicit agreement.

4. **Re-measure.** Run the script on all affected files: those of the argument and every other file the change
   edited or created. A deleted file ends at 0. The combined total is lower than the combined baseline, or the
   change is reverted. So is one that failed step 3.

5. **Report.** Per affected file and combined: tokens before, after and the difference. Then what verified the
   equivalence (which tests, which direct comparisons), and every proposal that was dropped, with the reason.
