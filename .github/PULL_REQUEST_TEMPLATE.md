## What this changes

<!-- One or two sentences. For a correction, state what was wrong. -->

## How you established it

<!-- For a correction to a CORRECT block, this is the important part.
     A numerical demonstration, a link to the library source, a citation. -->

## Checks

- [ ] `python scripts/validate_skills.py` passes
- [ ] `python scripts/generate_chapter_map.py` leaves no diff
- [ ] `python -m unittest discover -s tests` passes
- [ ] `pipx run ruff check .` passes
- [ ] The skill is 120 lines or fewer and has WRONG, CORRECT, Guardrails, Checklist
- [ ] No `ml4t.*` import before `## Production Implementation`

<!-- CI runs all of these. Ticking them first saves a round trip. -->
