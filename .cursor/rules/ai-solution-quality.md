# AI solution quality and risk communication

This rule applies to **all AI-assisted code generation and edits** (e.g. Cursor, agents). The goal is production-quality solutions, no workarounds, and clear communication when a solution is suboptimal or when no proper solution exists.

## Standards for solutions

- **Optimal over quick:** Prefer the correct, maintainable solution that fits the architecture (e.g. CQRS, layers in `.cursor/rules/project.md`) over a quick fix or workaround.
- **No workarounds as solutions:** Do not propose or implement workarounds (e.g. silencing errors, bypassing validation, or “temporary” hacks) as the primary solution. If the only way to meet a request is a workaround, treat it as “no proper solution” and follow the risk communication steps below.
- **System design and high standards:** Design and code as a senior software engineer would: clear boundaries, single responsibility, proper error handling, and alignment with project rules (CQRS, FastAPI patterns, database-postgres, etc.). See `.cursor/rules/clean-code.md`, `.cursor/rules/code-quality.md`, and `.cursor/rules/standards.md`.
- **Non-quirky:** Avoid unusual or fragile patterns (e.g. relying on undocumented behavior, heavy use of reflection or string-based dispatch where types or explicit code are clearer). Prefer standard, readable patterns used elsewhere in the project.

## When the solution is suboptimal or risky

If the only feasible approach is:
- suboptimal (e.g. performance trade-off, technical debt), or
- a workaround, or
- not fully aligned with project standards,

then **do not implement it without explicit developer acceptance.**

1. **Stop and warn:** Clearly state what is suboptimal or risky (e.g. “This uses a workaround because …”, “This will add technical debt because …”, “This violates [rule] because …”).
2. **Explain impact:** Briefly explain the impact (maintainability, performance, future refactors, etc.).
3. **Ask:** Ask the developer whether they want to proceed despite the risks (e.g. “Do you want to proceed with this approach? Reply yes to accept the trade-off.”).
4. **Proceed only after acceptance:** If the user confirms (e.g. “yes”, “proceed”), then implement and, if useful, add a short comment or TODO in code pointing to the trade-off. If the user does not confirm, suggest alternatives or state that no proper solution is available under the current constraints.

## When no proper solution exists

If there is **no** correct or maintainable solution under the given constraints (e.g. requirement conflicts with architecture, or would require a workaround only):

1. **Say so clearly:** “There is no proper solution that fits the project’s standards for [reason].”
2. **Summarize options:** Briefly list options (e.g. “Option A: workaround with risk X. Option B: change requirement Y.”).
3. **Do not implement a hack by default:** Do not implement a workaround or hack unless the user explicitly accepts the risk (see above).

## Checklist before finalizing (for AI and developers)

- [ ] Solution is not a workaround presented as the main fix.
- [ ] Solution fits project structure and rules (CQRS, layers, imports, style).
- [ ] If suboptimal or risky, the developer was warned and accepted.
- [ ] If no proper solution exists, that was stated and the user chose how to proceed.

## Reference

- Plan and strategy: `docs/AI_CODING_STANDARDS.md`
- Quality and scope: `.cursor/rules/code-quality.md`, `.cursor/rules/clean-code.md`
- Project structure: `.cursor/rules/project.md`, `.cursor/rules/standards.md`
- Agent skill: `.cursor/skills/ai-solution-quality/SKILL.md` (checklist and examples)
