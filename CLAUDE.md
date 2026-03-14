# ML4T Skills — Agent Entry Point

This repository's authoritative agent guidance lives in:

- `AGENTS.md` for repo-wide authoring rules and current project goals
- `.claude/CLAUDE.md` for Claude-specific repo instructions

Current project state:

- The repo contains 66 `SKILL.md` files across 10 categories.
- The active objective is to keep every skill concept-first and every `## Production Implementation` snippet aligned with the current checked-in `ml4t-*` library source under `~/ml4t/libraries/`.
- When a skill snippet conflicts with library source, treat the library source as ground truth and update the skill/docs.
- No `ml4t.*` imports may appear before `## Production Implementation`.

Agent infrastructure in this repo:

- Claude config: `.claude/CLAUDE.md` and `.claude/settings.json`
- Codex/OpenAI config: `AGENTS.md`
- There is no repo-local `.agents/` directory checked in here.
