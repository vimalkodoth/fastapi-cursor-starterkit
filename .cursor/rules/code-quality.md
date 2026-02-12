# Code quality

Guidelines for edits and code changes. Apply when modifying code (human or agent).

## Verify before changing

- Verify context and requirements before making changes. Do not assume or invent behavior.

## Scope of edits

- Prefer file-by-file changes so mistakes are easier to spot.
- Preserve existing code and behavior; do not remove or change unrelated logic.
- Do not invent features or changes beyond what was requested.

## Single coherent edits

- Provide complete edits in one go per file instead of multi-step partial instructions.

## No unnecessary churn

- Do not suggest updates when no real change is needed.
- Do not propose whitespace-only or cosmetic changes unless explicitly asked.
