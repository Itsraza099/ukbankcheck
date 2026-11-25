.PHONY: install lint format typecheck test check tables

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy

test:
	UKBANKCHECK_DATA_DIR=.vocalink uv run pytest

check: lint typecheck test

# Download Vocalink's tables into ./.vocalink (gitignored) for the spec tests.
tables:
	uv run python -m ukbankcheck download --dest .vocalink
