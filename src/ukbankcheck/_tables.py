"""Load and look up Vocalink's modulus weight table and sorting code substitution table.

The tables are not shipped with this package (see docs/decisions/0002). Download them with
``python -m ukbankcheck download`` or point :func:`load_tables` at your own copies.
"""

from __future__ import annotations

import os
from bisect import bisect_right
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from itertools import pairwise
from pathlib import Path

WEIGHTS_FILE = "valacdos.txt"
SUBSTITUTIONS_FILE = "scsubtab.txt"
DATA_DIR_ENV = "UKBANKCHECK_DATA_DIR"


class Method(str, Enum):
    """The three check methods in the weight table."""

    MOD10 = "MOD10"
    MOD11 = "MOD11"
    DBLAL = "DBLAL"  # double alternate


class TableFormatError(ValueError):
    """A line in a Vocalink data file isn't in the documented format."""


class TablesNotFoundError(FileNotFoundError):
    """The Vocalink data files haven't been downloaded yet."""


@dataclass(frozen=True)
class WeightRule:
    """One row of the weight table: a sort code range, a method, 14 weights, an exception."""

    start: int
    end: int
    method: Method
    weights: tuple[int, ...]
    exception: int | None = None

    def covers(self, sort_code: int) -> bool:
        return self.start <= sort_code <= self.end


@dataclass(frozen=True)
class ModulusTables:
    """Both Vocalink tables, validated and indexed for fast lookup."""

    rules: tuple[WeightRule, ...]
    substitutions: dict[str, str] = field(default_factory=dict)
    _starts: tuple[int, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        _check_no_overlaps(self.rules)
        object.__setattr__(self, "_starts", tuple(r.start for r in self.rules))

    def rules_for(self, sort_code: str) -> list[WeightRule]:
        """Return the one or two rules for a sort code, in table order (empty if none).

        Binary search instead of a scan: the table is sorted by start, and ranges never
        overlap, so the only candidate is the last range starting at or before the code.
        """
        code = int(sort_code)
        i = bisect_right(self._starts, code)
        if i == 0:
            return []
        candidate = self.rules[i - 1]
        if not candidate.covers(code):
            return []
        same = [r for r in self.rules[max(0, i - 2) : i] if r.start == candidate.start]
        return same


def _check_no_overlaps(rules: Sequence[WeightRule]) -> None:
    """Rules must be sorted, and ranges may only repeat exactly (for a second check)."""
    for prev, cur in pairwise(rules):
        if cur.start < prev.start:
            raise TableFormatError(f"rules out of order at {cur.start:06d}")
        same_range = (cur.start, cur.end) == (prev.start, prev.end)
        if not same_range and cur.start <= prev.end:
            raise TableFormatError(
                f"range {cur.start:06d}-{cur.end:06d} overlaps {prev.start:06d}-{prev.end:06d}"
            )


def parse_weights(lines: Iterable[str]) -> tuple[WeightRule, ...]:
    """Parse valacdos.txt. Each line: start end method w1..w14 [exception]."""
    rules = []
    for number, line in enumerate(lines, start=1):
        parts = line.split()
        if not parts:
            continue
        if len(parts) not in (17, 18):
            raise TableFormatError(f"line {number}: expected 17 or 18 fields, got {len(parts)}")
        try:
            start, end = int(parts[0]), int(parts[1])
            method = Method(parts[2].upper())
            weights = tuple(int(w) for w in parts[3:17])
            exception = int(parts[17]) if len(parts) == 18 else None
        except ValueError as exc:
            raise TableFormatError(f"line {number}: {exc}") from exc
        if start > end:
            raise TableFormatError(f"line {number}: start {start:06d} is after end {end:06d}")
        rules.append(WeightRule(start, end, method, weights, exception))
    if not rules:
        raise TableFormatError("weight table is empty")
    return tuple(rules)


def parse_substitutions(lines: Iterable[str]) -> dict[str, str]:
    """Parse scsubtab.txt. Each line: original_sort_code substitute_sort_code."""
    subs = {}
    for number, line in enumerate(lines, start=1):
        parts = line.split()
        if not parts:
            continue
        if len(parts) != 2 or not all(p.isdigit() and len(p) == 6 for p in parts):
            raise TableFormatError(f"line {number}: expected two 6-digit sort codes")
        subs[parts[0]] = parts[1]
    return subs


def default_data_dir() -> Path:
    """Where downloaded tables live: $UKBANKCHECK_DATA_DIR, else the user cache directory."""
    if env := os.environ.get(DATA_DIR_ENV):
        return Path(env)
    cache = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(cache) / "ukbankcheck"


def load_tables(directory: Path | None = None) -> ModulusTables:
    """Load both tables from ``directory`` (default: :func:`default_data_dir`)."""
    directory = directory or default_data_dir()
    weights_path = directory / WEIGHTS_FILE
    subs_path = directory / SUBSTITUTIONS_FILE
    if not weights_path.exists() or not subs_path.exists():
        raise TablesNotFoundError(
            f"Vocalink tables not found in {directory}. Run `python -m ukbankcheck download` first."
        )
    return ModulusTables(
        rules=parse_weights(weights_path.read_text().splitlines()),
        substitutions=parse_substitutions(subs_path.read_text().splitlines()),
    )
