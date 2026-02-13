# Agent Skills — multi-tool compatibility

This project uses the [Agent Skills open standard](https://agentskills.io) so the same skills work with **Cursor**, **Claude**, and **Codex** (and any other tool that supports the standard).

## Where skills live

| Tool   | Project-level path      | How this repo supports it |
|--------|--------------------------|----------------------------|
| Cursor | `.cursor/skills/`       | **Canonical** — skills are stored here. |
| Claude | `.claude/skills/`        | Symlink to `.cursor/skills/` so Claude discovers the same skills. |
| Codex  | `.codex/skills/`         | Symlink to `.cursor/skills/` so Codex discovers the same skills. |

**Single source of truth:** All skill content lives under `.cursor/skills/`. Each skill is a folder containing a `SKILL.md` file (see [Cursor Docs: Skills](https://cursor.com/docs/context/skills)). `.claude/skills` and `.codex/skills` point to that folder so you don’t maintain duplicates.

## Why not `.agents/skills/`?

Cursor’s official docs list these discovery paths:

- **Project:** `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`
- **User (global):** `~/.cursor/skills/`, `~/.claude/skills/`, `~/.codex/skills/`

There is no `.agents/skills/` in the standard. Tools auto-discover skills only from the paths above. Using `.cursor/skills/` (and symlinks for Claude/Codex) keeps one copy of each skill and works with all of them.

## If symlinks don’t work (e.g. some Windows setups)

If your environment doesn’t support symlinks or they don’t clone correctly:

1. **Cursor:** Use `.cursor/skills/` as-is (no change).
2. **Claude / Codex:** Copy the contents of `.cursor/skills/` into `.claude/skills/` or `.codex/skills/` (create the directory and copy the skill folders). Keep them in sync when you add or change skills.

## Adding or changing skills

1. Edit or add skill folders under **`.cursor/skills/`** only.
2. Each skill is a folder (e.g. `ai-solution-quality/`) with a **`SKILL.md`** file and optional `scripts/`, `references/`, `assets/`.
3. Commit changes. With symlinks, `.claude/skills/` and `.codex/skills/` automatically see the same content.

## References

- [Cursor: Agent Skills](https://cursor.com/docs/context/skills) — discovery paths, SKILL.md format, optional dirs.
- [Cursor blog: Best practices for coding with agents](https://cursor.com/blog/agent-best-practices) — Rules vs Skills, when to use each.
- [Agent Skills standard](https://agentskills.io) — open standard for portable, version-controlled skills.
