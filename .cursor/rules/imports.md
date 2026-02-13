# Imports — Top of file and ordered

Apply to **all Python files** in `backend/`, `services/`, and any other project Python code. Enforced by isort and flake8 (E402) where applicable; this rule makes the convention explicit for AI and developers.

## Rule: All imports at top of file only

- **Every import must be at the top of the file.** No imports inside functions, inside classes, or after any executable code (except in type-checking blocks — see below).
- **Order:** Group and order imports in three blocks, with a single blank line between blocks:
  1. **Standard library** — `import os`, `from typing import Optional`, etc. Alphabetical within the block.
  2. **Third-party / external libraries** — `from fastapi import APIRouter`, `from sqlmodel import Session`, etc. Alphabetical within the block.
  3. **Local / project imports** — `from app.core.database import engine`, `from app.models.schemas import DataRequest`, etc. Alphabetical within the block.
- Use **absolute imports** for project code (e.g. `from app.services.data_service import DataService`), not relative imports like `from ...services import ...`, unless the project explicitly allows it.
- **isort** is configured for this project; run `make format` from repo root so import order matches the above. Do not add `# noqa` or equivalent to bypass import order or “import not at top” (E402) unless there is a documented, rare exception (e.g. optional dependency that may be missing at runtime).

## Correct example

```python
"""Module docstring."""
import json
from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import engine
from app.models.schemas import DataRequest
from app.services.data_service import DataService

# Executable code and definitions follow; no more imports below.
```

## Incorrect examples

- **Wrong:** Import inside a function or after code.
  ```python
  def process():
      import os  # BAD
      from app.core import config  # BAD
  ```
- **Wrong:** Third-party before standard library, or project imports mixed with library imports.
  ```python
  from fastapi import APIRouter  # BAD: put stdlib first
  import os
  from app.core import config
  ```
- **Wrong:** Using `# noqa: E402` or similar to allow mid-file imports without a justified, documented exception.

## Optional / conditional imports

- If the project requires an optional dependency that may be missing (e.g. `optional_package`), use a **single** try/except block at the top of the file and keep all other imports at top. Document why the import is conditional. Do not scatter optional imports in the middle of the file.
- Example:
  ```python
  import os
  from typing import Optional

  try:
      from optional_package import something
  except ImportError:
      something = None  # Document: used when optional_package is installed
  ```

## Reference

- Format/lint: run `make format` and `make lint` from repo root (see `.cursor/rules/commands-and-workflow.md`).
- Style: `.cursor/rules/python-style.md`, `.cursor/rules/standards.md`.
