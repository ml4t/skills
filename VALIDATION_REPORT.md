# Skills Validation Report

**Date**: 2026-03-14
**Total skills**: 66
**Passed**: 65
**Failed**: 1
**Warnings**: 0

## Category Breakdown

| Category | Count | Status |
|----------|-------|--------|
| advanced-ai | 5 | All pass |
| backtest | 6 | All pass |
| concepts | 10 | 1 failure |
| data | 8 | All pass |
| features | 10 | All pass |
| infrastructure | 4 | All pass |
| portfolio | 6 | All pass |
| production | 4 | All pass |
| validation | 8 | All pass |
| workflows | 5 | All pass |
| **Total** | **66** | **65/66 pass** |

## Per-Check Summary

| # | Check | Pass | Fail | Description |
|---|-------|------|------|-------------|
| 1 | File exists | 66 | 0 | SKILL.md present in directory |
| 2 | Frontmatter valid | 65 | 1 | Has `name`, `description`, `dependencies`, `metadata` with `book_chapters` |
| 3 | No banned fields | 65 | 1 | No `quantlab_module`, `category`, or `type` fields |
| 4 | Name matches | 66 | 0 | `name` field equals `ml4t-{directory-name}` |
| 5 | 80/20 split | 66 | 0 | No `from ml4t.` import before "Production Implementation" |
| 6 | WRONG/CORRECT pair | 65 | 1 | Both `### WRONG` and `### CORRECT` headers present |
| 7 | Checklist | 66 | 0 | `## Checklist` section exists |
| 8 | Line count | 66 | 0 | Under 200 lines (none exceed 180) |
| 9 | No QuantLab | 66 | 0 | No occurrence of "QuantLab" |

## Failures

### concepts/lookahead-bias (4 violations)

This is the only skill still in the old pre-migration format. It needs to be rewritten to match the current template.

| Check | Issue |
|-------|-------|
| Frontmatter valid | `book_chapters` at top level instead of under `metadata:` |
| No banned fields | Has `category: concepts` in frontmatter |
| No banned fields | Has `type: conceptual` in frontmatter |
| WRONG/CORRECT pair | Uses `# WRONG` / `# CORRECT` as code comments inside fenced blocks, not as `### WRONG` / `### CORRECT` markdown headers |

## Line Count Analysis

| Metric | Value |
|--------|-------|
| Minimum | 67 lines (concepts/lookahead-bias -- the outlier) |
| Maximum | 120 lines |
| Average | 108 lines |
| Median | 110 lines |
| Target | 120 lines |
| Warning threshold (>180) | 0 skills |
| Hard limit (>200) | 0 skills |

All 65 conformant skills fall in the 90-120 line range, well within the target.

## Methodology

Validation was performed programmatically via a bash script checking all 9 conditions across all 66 skill directories in `/home/stefan/ml4t/skills/`. Each SKILL.md file was checked for:

1. File existence
2. YAML frontmatter field presence (parsed between `---` delimiters)
3. Absence of banned frontmatter fields via regex match on `^field:`
4. Name field match against `ml4t-{directory-name}`
5. No `from ml4t.` imports appearing before the "Production Implementation" header line
6. Presence of `### WRONG` and `### CORRECT` (or `####` variants) as markdown headers
7. Presence of `## Checklist` header
8. Total line count under 200 (warning at 180)
9. Case-insensitive grep for "QuantLab"
