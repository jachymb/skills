---
name: cut-the-fluff
description: Condense a text for its actual readers, keeping only the information they really need and improving clarity. Not a summary. Use when the user asks to shorten, condense, tighten, trim, de-fluff or "cut the fluff" from a text, says it is too long or hard to read, wants it readable for a given audience, or invokes /cut-the-fluff. The argument names the file, page or issue, optionally the audience, or gives instructions for the text last edited in the session.
argument-hint: "[file | URL | issue key] [audience] [instructions]"
---

# Cut the fluff

Argument: `$ARGUMENTS`

The reader's time and attention are scarce, and the reader has a job to do with the text: review, decide, act or look something up. Keep what that job needs, in their terms, and drop only the rest.

This is not a summary. A summary trades detail for brevity; here every detail the job needs stays, exact, and the text gets shorter only by losing what the reader does not need.

## Method

Apply these steps in order:

1. Identify the target text.
2. Identify the target audience.
3. Cut what the reader doesn't need.
4. Have a subagent check the result.
5. Write.
6. Report.

## 1. Target text

Unless the instructions in the argument say otherwise, the target depends on what the argument names:

- **A document file, message or similar:** that file or text.
- **A source code file:** its docstrings, comments and other free text, never the code itself.
- **A configuration or data file:** not a target; say so and stop.
- **A page or issue** (Confluence, Jira, wiki): read it with the session's skill or API, save the original, and edit a copy in its own format. Before writing a new version, re-read the live one and merge newer edits; afterwards check that it renders. Confirm per the system's rules; without any, naming the page is the permission.
- **Nothing named, or only instructions:** the text most recently created or edited in the session. Ask if that is ambiguous.

## 2. Target audience

Knowing the audience is crucial to tailoring the text to their needs, interests and level of understanding. Infer it from the session context, the target text and the instructions in the argument, and settle:

- who reads the text: their role (for example maintainer or reviewer, developer on the same or another team, business user, analyst, manager, specialist engineer, data scientist), and the project and general environment in which the text exists
- what they will do with it
- what they already know
- which words they use for the subject

Put the answers into an audience statement of one or two sentences, for example "Maintainers of the upstream library, reviewing this PR; they know the codebase but not our use case." Steps 3, 4 and 6 use it.

If several roles are expected, write the text so that all of them understand it, and put any necessary specialised detail in sections at the bottom of the document.

Ask the user only when the possible audiences would lead to different texts. Otherwise proceed and state the assumption in the report.

## 3. Cut

First, consider the document's overall structure. Lead with what the reader came for: the decision, result or request. Detail follows. Restructuring the whole document is allowed, as long as it improves clarity and makes the text simpler or easier to read. The shape the text must have survives any restructuring: its template and required sections, frontmatter, markup and language.

Then consider what the reader would find irrelevant, uninteresting or too verbose.

Always drop:

- Common knowledge for the reader.
- Repetition.
- Hedges, signposts, preambles and closers that carry no information.
- Excerpts that a link to their source can replace, when you know the link and the reader can open it.

Often drop, depending on context:

- **Superseded passages**, which describe a past state rather than the current one.
- **The journey** ("I first checked..."). State the result. Keep the process only when it is the content.
- **Options not taken**, unless the reader must choose between them.
- **Caveats** about things that did not happen.

Keep, even where a rule above says to drop, unless the instructions say otherwise:

- **Names, paths, commands, links and error text.** Code blocks stay verbatim or go whole. Which identifiers stay depends on the audience; move rather than delete what someone may look for.
- **Exact numbers.**
- **Real uncertainty**, if deleting it would change what the reader may conclude.
- **Claims at their original strength.** Never strengthen one: no "always" for "in the cases tested", no dropped conditions.
- **Limitations, behaviour changes, and text the reader reuses as is.**
- **Unclear passages.** Keep them as written, or ask. Flag errors in the reply instead of fixing them.

Beyond the cuts, consider where rewording would make the text easier for the audience to understand. Replace jargon the reader may not know with plain words, or define it once. Otherwise add nothing: no facts or claims that the original lacks.

If the text is already tight, say so and change nothing.

## 4. Check

Save the draft to a scratch file, and the original too if it is not already a file; the target itself stays untouched until step 5. Then have a subagent review the draft critically. Give it the audience statement and the paths of the draft and the original, tell it that this skill produced the draft, and have it work in this order:

1. Read only the draft, as the audience, and note what is unclear, what they would still need for their job, and what could still be cut.
2. Then read the original and list every fact, number, name or caveat that the draft lacks or states at a different strength.

Consider the subagent's remarks and incorporate the worthwhile ones. One round is enough; do not send the revision back.

For a short text, such as a single comment or a message of a few lines, skip the subagent and do both passes yourself.

## 5. Write

Write the file, or use the appropriate API to post the text where it belongs.

## 6. Report

Report:

- the audience statement, and whether the audience was given or assumed
- a reference to the written text (file name or URL)
- the size in words, before and after
- the judgment calls: what was dropped or moved on a close call
- errors and unclear passages found in the original
