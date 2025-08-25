# Contributing

Thanks for helping! This repo is intentionally small and focused. Please read this before opening a PR.

## Quick start (dev setup)

```bash
# clone your fork
git clone https://github.com/<you>/shopify-gql-helper-py
cd shopify-gql-helper-py

# install package + dev tools
python -m pip install --upgrade pip
pip install -e ".[dev]"

# run tests
pytest -q
```

## What PRs are welcome
- Bug fixes and small improvements to:
  - per-shop throttling behavior
  - `execute()` retry/error handling
  - `cursor_pages()` pagination
- Docs/README improvements
- Test coverage (fixtures, edge cases)

### Out of scope (open an issue first)
- Bulk Operations
- Async/Redis/queues
- Deep nested auto-pagination
- OAuth/CLI

## Code style
- Keep it **simple** and small.
- Type hints on public functions/classes.
- Add short docstrings where it helps editors/hover.
- Black/PEP8-friendly formatting.

## Tests
- Add/adjust tests for your change (`tests/`).
- `pytest -q` must pass locally and in CI.
- No network calls in tests; use fixtures/mocks.

## `pyproject.toml`
- OK to propose:
  - dev extras (`.[dev]`), classifiers, metadata
  - dependency tweaks with justification
- **Do not bump `version`** in PRs (maintainers handle releases).
- Keep runtime deps minimal.

## Commit & PR
- One logical change per PR.
- Commit messages: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`
- Link related issues (e.g., “Fixes #12”).
- PR checklist:
  - [ ] Code compiled/ran locally
  - [ ] Tests updated/passing
  - [ ] Docs/README touched if behavior changed

## Release process
- Maintainers cut Releases.
- Tagging a Release triggers:
  - Build → TestPyPI publish → smoke import
  - If not a “pre-release”, publish to PyPI
- Contributors: **don’t** change version or push tags.

## Conduct
Be kind. Disagree on code, not people.
