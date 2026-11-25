.PHONY: install lint format typecheck test check tables web serve

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

# Build the package into web/ and serve the in-browser checker at http://localhost:8000
web:
	rm -f web/*.whl
	uv build --wheel --out-dir web
	rm -f web/.gitignore  # uv writes one that would hide the whole page from git
	cd web && ls *.whl | head -1 | sed 's/.*/{"file": "&"}/' > wheel.json

serve: web
	uv run python -m http.server 8000 --directory web
