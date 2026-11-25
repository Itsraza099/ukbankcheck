"""Shared fixtures.

The real Vocalink tables aren't committed (see docs/decisions/0002). Tests that need them
look in $UKBANKCHECK_DATA_DIR. Locally they're skipped if the files are missing; in CI,
UKBANKCHECK_REQUIRE_TABLES=1 turns a skip into a failure so they can't silently not run.
"""

import os
from pathlib import Path

import pytest

from ukbankcheck import ModulusTables, TablesNotFoundError, load_tables


@pytest.fixture(scope="session")
def real_tables() -> ModulusTables:
    directory = os.environ.get("UKBANKCHECK_DATA_DIR")
    try:
        return load_tables(Path(directory) if directory else None)
    except TablesNotFoundError:
        if os.environ.get("UKBANKCHECK_REQUIRE_TABLES") == "1":
            raise
        pytest.skip("Vocalink tables not downloaded (run `make tables`)")
