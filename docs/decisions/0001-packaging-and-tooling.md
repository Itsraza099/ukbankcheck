# 0001. Packaging and tooling

- Status: Proposed
- Date: 2026-11-25

## Context
This is a small, dependency-free library meant to be installed from PyPI. It is
also practice for the habits every other repo in the portfolio reuses.

## Decision
- `src/` layout, so tests run against the installed package, not the working folder.
- `pyproject.toml` with the **hatchling** build backend; **uv** for environments and locking.
- **ruff** for linting and formatting, **mypy --strict** for types, **pytest** + **Hypothesis**.
- CI runs on Python 3.10–3.13 and fails below 90% test coverage.
- Releases publish from a git tag through PyPI **trusted publishing** (no stored token).

## Alternatives considered
- setuptools: works, but more configuration for no gain here.
- Poetry: popular, but uv is faster and uses standard `pyproject.toml` fields.
- flake8 + black + isort: three tools where ruff does the job of all three.
- A PyPI API token in GitHub secrets: a long-lived secret that can leak; trusted publishing avoids it.

## Consequences
Contributors need uv installed. Supporting four Python versions means CI runs four jobs.
