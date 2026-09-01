# Contributing

Outside contributions are welcome. This file says what a good one looks like
and how to check your work before opening a pull request.

`AGENTS.md` is the authoring specification and the final word on any rule
summarised here.

## What belongs in this repository

A skill earns its place by preventing a specific, expensive mistake that a
capable coding agent makes anyway. The test is not "is this true about quant
finance" but "would an agent get this wrong without being told, and would the
result look plausible enough to ship".

Good candidates:

- A failure mode with a concrete WRONG example that a reviewer would recognise.
- A correction expressible in standard tools, in roughly 120 lines.
- Something the book develops in full, so `metadata.book_chapters` has an answer.

Poor candidates:

- General Python or ML advice with no financial failure mode attached.
- A wrapper around a library call, with no method being taught.
- A method with no way to tell whether it was applied correctly.

## Before you open a pull request

Run the same checks CI runs:

```bash
python scripts/validate_skills.py       # structure, frontmatter, hygiene
python scripts/generate_chapter_map.py  # regenerate SKILL_CHAPTER_MAP.md
python -m unittest discover -s tests    # the repository's own scripts
pipx run ruff check .                   # lint
```

To also check `## Production Implementation` snippets against the published
library APIs, which is what the `api-accuracy` CI job does:

```bash
python -m pip download --no-deps --only-binary=:all: --dest wheels \
  ml4t-data ml4t-engineer ml4t-backtest ml4t-diagnostic ml4t-live
mkdir -p library-src
for wheel in wheels/*.whl; do python -m zipfile -e "$wheel" library-src; done
python scripts/validate_skills.py --library-root library-src
```

If you have the libraries checked out locally instead, point `--library-root`
at the directory holding the `ml4t-*` repositories.

## The rules the validator enforces

- One file, `SKILL.md`, in its own directory under an existing category.
- `name: ml4t-<directory-name>`, matching the directory exactly.
- `description` written in the third person and containing "Use when", so
  runtimes that match implicitly can find it.
- `metadata.book_chapters` naming at least one chapter between 1 and 27.
- 120 lines or fewer, including frontmatter. Longer material goes in a
  `references/` subdirectory.
- A `### WRONG` and a `### CORRECT` heading, a `## Guardrails` section, and a
  `## Checklist` as the last section.
- No `ml4t.*` import anywhere before `## Production Implementation`. The first
  four fifths of a skill teaches the method in standard tools; the library is
  the handoff, not the lesson.
- Every name imported from `ml4t.*` must exist in the published package.
- `dependencies` naming skills that exist, with no cycles.

## Style

- Teach the method, not the library. A reader without the `ml4t-*` packages
  installed should still learn something they can apply.
- The WRONG example has to be code someone would plausibly write. An obviously
  broken example teaches nothing.
- Guardrails are detection patterns, not encouragement. "Search for
  `fit_transform` before a split" is a guardrail; "be careful with scaling" is
  not.
- Prefer a plain dash to an em dash, and prose to a metaphor.

## Corrections to existing skills

Corrections are the most valuable contribution here, particularly when a
`### CORRECT` block is subtly wrong. Open an issue with the failure, or a pull
request with the fix and a sentence on how you established it. Say how you
checked: a numerical demonstration beats an assertion.

## Licensing

Contributions are accepted under the repository's [Apache-2.0](LICENSE)
licence, per section 5 of that licence. There is no separate CLA to sign. Do
not contribute material you do not have the right to license, and do not paste
text from the book or from another copyrighted source.

## Conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
