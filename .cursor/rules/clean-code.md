# Clean code

Apply when writing or reviewing code. Keeps code maintainable and consistent.

## Constants over magic numbers

- Replace hard-coded values with named constants.
- Use descriptive names that explain the value's purpose.
- Keep constants at module top or in a dedicated module (e.g. `constants.py`).

## Meaningful names

- Variables, functions, and classes should reveal their purpose.
- Names should explain why something exists and how it's used.
- Avoid abbreviations unless universally understood (e.g. `id`, `url`).

## Comments

- Don't comment what the code does; make the code self-documenting.
- Use comments to explain **why** something is done a certain way.
- Document public APIs, complex logic, and non-obvious side effects.

## Single responsibility

- Each function should do exactly one thing.
- Keep functions small and focused.
- If a function needs a comment to explain what it does, split it.

## DRY (Don't Repeat Yourself)

- Extract repeated code into reusable functions or helpers.
- Share common logic through clear abstractions.
- Maintain single sources of truth.

## Structure

- Keep related code together.
- Organize code in a logical hierarchy (see `.cursor/rules/project.md` for this repo).
- Use consistent file and folder naming (e.g. `snake_case` for modules).

## Encapsulation

- Hide implementation details behind clear interfaces.
- Move nested conditionals into well-named functions (guard clauses).

## Quality maintenance

- Refactor as you go.
- Fix technical debt early.
- Leave code cleaner than you found it.

## Testing

- Write tests before or when fixing bugs.
- Keep tests readable and maintainable.
- Cover edge cases and error paths.

## Version control

- Write clear commit messages.
- Prefer small, focused commits.
- Use meaningful branch names.
