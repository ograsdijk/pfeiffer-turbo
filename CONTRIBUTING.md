# Contributing

## Development

This project uses `uv` for local development.

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy pfeiffer_turbo
```

## Releases

Publishing is done from Git tags, not commit messages.

1. Update the version in `pyproject.toml`.
2. Merge the change to `main`.
3. Create and push a tag matching the package version, for example `v0.2.1`.

```bash
git tag -a v0.2.1 -m "Release v0.2.1"
git push origin v0.2.1
```

The publish workflow verifies that the tag matches the version in `pyproject.toml`, runs the test suite, builds the package, and uploads it to PyPI.

Configure PyPI Trusted Publishing for this repository before using the publish workflow.