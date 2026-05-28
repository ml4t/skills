# ML4T Skills — Agent Entry Point

This repository's authoritative agent guidance lives in:

- `AGENTS.md` for repo-wide authoring rules and current project goals

Current project state:

- The repo contains 61 `SKILL.md` files across 10 categories.
- The active objective is to keep every skill concept-first and every `## Production Implementation` snippet aligned with the published `ml4t-*` library APIs.
- When a skill snippet conflicts with library source, treat the library source as ground truth and update the skill/docs.
- No `ml4t.*` imports may appear before `## Production Implementation`.

Local agent infrastructure:

- Codex/OpenAI config: `AGENTS.md`
- Local project-management state belongs under `.workspace/`
- Runtime-specific state such as `.agents/`, `.claude/`, and `.codex/` is ignored and not part of the public distribution
