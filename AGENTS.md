# AGENTS.md

## Environment

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. All commands should be run via `uv run` so they use the project's virtual environment automatically — no need to activate `.venv` manually.

## Common commands

Run the test suite:

```
uv run pytest
```

Run the type checker:

```
uv run ty check
```

Run the linter:

```
uv run ruff check
```

Run the formatter:

```
uv run ruff format
```

Run the CLI:

```
uv run marctable
```
