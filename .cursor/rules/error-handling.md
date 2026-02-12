# Error handling

Prioritize errors and edge cases so the happy path stays clear and readable.

## Order of logic

- Handle **errors and edge cases at the beginning** of functions.
- Use **early returns** for error conditions to avoid deeply nested `if` blocks.
- Place the **happy path last** in the function.

## Guard clauses

- Use guard clauses for preconditions and invalid state.
- Avoid unnecessary `else` after `return`; use the **if–return** pattern.

## Consistency

- Use **custom exception types** or error factories where it helps consistency.
- In API layer: use **HTTPException** with appropriate status codes; map business errors to HTTP.

## Logging and messages

- Implement proper **error logging** (level, context).
- Return **user- or client-friendly error messages** where appropriate; avoid leaking internals.
