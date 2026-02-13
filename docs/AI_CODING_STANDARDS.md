# AI Coding Standards — Plan and Enforcement Strategy

This document describes how the team standardizes AI-assisted development (e.g. Cursor) so that generated code meets high engineering standards and avoids suboptimal or risky solutions.

## Goals

1. **Consistency:** All imports at top of file; library imports first, then project imports.
2. **Quality:** No workarounds or quirky solutions; optimal, maintainable solutions only.
3. **Risk transparency:** When a solution is suboptimal or no proper solution exists, the AI must clearly warn the developer and ask for explicit acceptance of risks before proceeding.
4. **Engineering standards:** System design and code should meet high software engineering standards; the AI should behave like a senior engineer.

## Research Summary: Enforcing AI Coding Standards

- **Version-controlled rules:** Keep all rules in `.cursor/rules/` and skills in `.cursor/skills/` under git so every team member and every AI session uses the same standards. Changes go through review like code.
- **Specific, imperative rules:** Vague guidelines (“write good code”) are ignored. Use concrete, imperative rules with correct vs incorrect examples (e.g. “All imports at top of file; no imports inside functions or after code.”).
- **Domain-scoped rules:** Organize rules by concern (imports, solution quality, Python style, CQRS) so the right rules apply in the right context. Reference rules from a central index (e.g. `project.md`).
- **Agent skills:** Use `.cursor/skills/` (discovered by Cursor; Claude/Codex via `.claude/skills/`, `.codex/skills/` symlinks) for deeper, checklist-style guidance. Skills are referenced when doing feature work or reviews. See `docs/AGENT_SKILLS.md`.
- **Pre-commit and CI:** Enforce style and lint (black, isort, flake8) so that import order and style are automatically enforced even if the AI slips. This backs up the rules.
- **Explicit “do not” list:** State what the AI must not do (e.g. no mid-file imports, no workarounds, no proceeding on risky solutions without user confirmation). This reduces ambiguous behavior.
- **Risk confirmation:** Require the AI to stop and ask (“This approach has trade-off X. Do you want to proceed?”) when the only option is suboptimal or when no clean solution exists. Document this in rules so the model follows it consistently.

## Enforcement Mechanisms

| Mechanism | Purpose |
|-----------|---------|
| **`.cursor/rules/`** | Authoritative, project-specific rules the AI is instructed to follow. Covers imports, solution quality, and risk communication. |
| **`.cursor/skills/`** | Deeper checklists and patterns (e.g. anti-patterns, solution-quality skill). Used for feature work and code review. Multi-tool: `.claude/skills/`, `.codex/skills/` symlink to same content. |
| **`make format` / `make lint` / pre-commit** | Automatically fix or flag import order and style. Catches violations even if the AI forgets. |
| **Code review** | Reviewers check that changes follow rules (imports, no workarounds, risks documented). |
| **Docs (this file)** | Single place for the “why” and the plan; onboarding and rule owners refer to it. |

## Rule Overview

- **Imports:** `.cursor/rules/imports.md` — All imports at top of file only. Order: (1) standard library, (2) third-party, (3) local/project. No imports inside functions, classes, or after executable code. Use isort; no `# noqa` to bypass import order.
- **AI solution quality:** `.cursor/rules/ai-solution-quality.md` — Prefer optimal, non-workaround solutions. Before implementing a suboptimal or risky approach, warn the developer and ask for explicit acceptance. If no proper solution exists, say so and do not implement a hack without confirmation.
- **Existing rules:** `project.md`, `standards.md`, `python-style.md`, `code-quality.md`, `clean-code.md`, and others remain the source for structure, patterns, and style. The new rules add import discipline and AI behavior.

## Agent Skill

- **`.cursor/skills/ai-solution-quality/SKILL.md`** — Checklist for the AI (and developers) when implementing features: avoid workarounds, prefer proper design, communicate risks, ask before proceeding on suboptimal choices. Referenced in `project.md` and `.cursor/skills/README.md`.

## Maintenance

- **Rule owners:** Designate an owner (e.g. tech lead) for `.cursor/rules/` and `.cursor/skills/`. They update rules when patterns or frameworks change and resolve conflicts.
- **Feedback loop:** When the AI repeatedly violates a rule, strengthen the rule with a concrete example or add a “do not” line. Use CI and pre-commit to catch regressions.
- **Onboarding:** New team members read this doc and the linked rules; Cursor and agents then apply the same standards automatically.

## References

- Cursor rules best practices (team standards, modular rules, specific examples): e.g. Lambda Curry, Cursor.fan, PRPM.
- Project rules index: `.cursor/rules/project.md`.
- Skills alignment and multi-tool layout: `.cursor/skills/README.md`, `docs/AGENT_SKILLS.md`.
