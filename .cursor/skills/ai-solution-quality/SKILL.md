---
name: ai-solution-quality
description: Enforce optimal solutions, no workarounds, and clear risk communication when using AI for code. Use when implementing features, refactoring, or reviewing AI-generated code so the team maintains high engineering standards.
---

## In this repository

- **Rules:** `.cursor/rules/ai-solution-quality.md` (when to warn, ask, and not implement), `.cursor/rules/imports.md` (imports at top, ordered), `.cursor/rules/code-quality.md`, `.cursor/rules/clean-code.md`.
- **Plan:** `docs/AI_CODING_STANDARDS.md` — strategy and enforcement.
- After any code change: run **`make format`** and **`make lint`** from repo root.

---

# AI solution quality — checklist and examples

Use this skill when implementing a feature, fixing a bug, or reviewing code so that AI-assisted output is optimal, non-workaround, and risks are communicated.

## When to use this skill

- Implementing a new feature or endpoint
- Proposing a fix for a bug or regression
- Refactoring or changing architecture
- Reviewing or refining AI-generated code before merge
- When the user asks for something that might require a workaround or suboptimal approach

## Pre-implementation checklist

Before writing or proposing code, confirm:

1. **Imports:** All imports at top of file; order: standard library → third-party → project. No imports inside functions or after code. See `.cursor/rules/imports.md`.
2. **No workaround as solution:** The approach is a proper fix or feature that fits the architecture (CQRS, layers, DB, etc.), not a hack or bypass.
3. **Standards:** Solution aligns with `.cursor/rules/standards.md`, `.cursor/rules/project.md`, and domain rules (e.g. CQRS, FastAPI patterns).
4. **Risks:** If the only option is suboptimal or risky, the plan is to warn the user and ask for explicit acceptance before implementing (see below).

## Risk communication (mandatory)

When **any** of the following is true:

- The only feasible approach is a **workaround** (e.g. silencing an error, bypassing validation, or a “temporary” hack),
- The solution is **suboptimal** (e.g. known technical debt, performance trade-off, or deviation from project patterns),
- There is **no proper solution** under the current constraints,

then:

1. **Do not implement by default.** Stop and state clearly:
   - What is suboptimal or missing (e.g. “This would require a workaround because …”),
   - The impact (maintainability, performance, future refactors),
   - That you need explicit acceptance to proceed.
2. **Ask:** “Do you want to proceed with this approach despite the risks? Reply yes to accept.”
3. **Implement only after** the user confirms (e.g. “yes”, “proceed”). If they do not confirm, suggest alternatives or state that no proper solution exists and what would be required (e.g. requirement change, dependency upgrade).

## Examples

### Example: Workaround vs proper fix

- **Bad:** User asks to “make the timeout errors go away.” AI adds a broad `try/except` that swallows errors and returns a generic message — no proper handling, no logging, no retry policy.
- **Good:** AI explains that “making errors go away” without proper handling would be a workaround, and that the proper approach is: define timeout/retry policy, log failures, and return a clear client response. AI then implements the proper approach or asks whether the user wants a temporary workaround and documents the risk.

### Example: Suboptimal design

- **Bad:** User asks for a new report that requires a heavy join. AI adds a N+1 loop in the API handler “because it’s faster to write.”
- **Good:** AI proposes a single query or a dedicated read model (CQRS) and implements it. If the only option is N+1 due to constraints, AI says: “The only option with current schema is N+1, which will not scale. Proceed anyway? (yes/no)” and implements only if the user accepts.

### Example: No proper solution

- **Bad:** User asks to “store secrets in the repo for local dev.” AI adds a `secrets.json` and commits it.
- **Good:** AI states that storing secrets in the repo violates security standards and that there is no proper solution that does that. AI suggests alternatives (env vars, local override file in `.gitignore`, secret manager) and does not implement the insecure option unless the user explicitly accepts the risk and documents it.

## Alignment with other skills

- **fastapi-best-practices:** Use for API structure and patterns; this skill ensures those patterns are applied without workarounds.
- **cqrs-pattern:** Use for command/query separation; this skill ensures CQRS is not bypassed for “quick” fixes.
- **python-anti-patterns:** Use to avoid known bad patterns; this skill ensures the AI does not introduce new ones and communicates when it must deviate.

No skill should suggest: ignoring project rules, implementing workarounds without warning, or proceeding on risky solutions without explicit user acceptance.
