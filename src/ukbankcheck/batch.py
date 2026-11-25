"""Check a whole CSV of bank details at once.

Used by ``python -m ukbankcheck check-file`` and by the in-browser checker (web/), so both
produce exactly the same results.

Input: a CSV with a sort code column and an account number column (header names are
matched loosely, e.g. "Sort Code" or "sort_code"). Every other column is passed through
untouched. Output: the same rows plus four columns:

- ``sort_code_clean`` / ``account_number_clean``: the canonical digits, if readable
- ``outcome``: valid, invalid, not_checked, foreign_currency, needs_review or bad_format
- ``reason``: a plain-English explanation
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass, field

from ukbankcheck._modulus import Outcome, check
from ukbankcheck._normalise import InvalidFormatError
from ukbankcheck._tables import ModulusTables

SORT_CODE_HEADERS = {"sortcode", "sortcodes", "sc", "bankcode"}
ACCOUNT_HEADERS = {"accountnumber", "accountno", "account", "accno", "acno", "accountnum"}
ADDED_COLUMNS = ["sort_code_clean", "account_number_clean", "outcome", "reason"]
MAX_ROWS = 200_000

NEEDS_REVIEW = "needs_review"
BAD_FORMAT = "bad_format"
OUTCOME_ORDER = [
    Outcome.VALID.value,
    Outcome.INVALID.value,
    Outcome.NOT_CHECKED.value,
    Outcome.FOREIGN_CURRENCY.value,
    NEEDS_REVIEW,
    BAD_FORMAT,
]

REASONS = {
    Outcome.VALID: "Passes the modulus check for this sort code.",
    Outcome.INVALID: "Fails the modulus check: probably a typo in the sort code or account.",
    Outcome.NOT_CHECKED: "No modulus rules for this sort code, so it can't be checked.",
    Outcome.FOREIGN_CURRENCY: "Foreign currency account: these can't be modulus checked.",
}

_SCIENTIFIC = re.compile(r"^\d(\.\d+)?[eE]\+?\d+$")


class BatchError(ValueError):
    """The file can't be processed at all (for example, required columns are missing)."""


@dataclass
class BatchResult:
    rows: list[dict[str, str]]
    columns: list[str]
    summary: Counter[str] = field(default_factory=Counter)

    def to_csv(self) -> str:
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=self.columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(self.rows)
        return out.getvalue()


def _key(header: str) -> str:
    return re.sub(r"[^a-z]", "", header.lower())


def _find_column(headers: list[str], names: set[str], label: str) -> str:
    for header in headers:
        if _key(header) in names:
            return header
    raise BatchError(f"no {label} column found (columns are: {', '.join(headers) or 'none'})")


def _excel_damage(sort_code: str, account: str) -> str | None:
    """Spot values that spreadsheet software has probably mangled. Flag, never guess."""
    for value, label in ((sort_code, "sort code"), (account, "account number")):
        if _SCIENTIFIC.match(value.strip()):
            return (
                f"The {label} looks like scientific notation ({value.strip()}), "
                "as Excel writes long numbers."
            )
    if sort_code.strip().isdigit() and len(sort_code.strip()) == 5:
        return (
            "The sort code has 5 digits: Excel probably removed a leading zero. "
            "Check the original and format the column as text."
        )
    return None


def check_rows(csv_text: str, tables: ModulusTables) -> BatchResult:
    """Check every row of ``csv_text``. Blank rows are skipped."""
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("﻿")))
    headers = [h for h in (reader.fieldnames or []) if h is not None]
    sc_col = _find_column(headers, SORT_CODE_HEADERS, "sort code")
    acc_col = _find_column(headers, ACCOUNT_HEADERS, "account number")

    columns = headers + [c for c in ADDED_COLUMNS if c not in headers]
    result = BatchResult(rows=[], columns=columns)

    for row in reader:
        if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
            continue
        if len(result.rows) >= MAX_ROWS:
            raise BatchError(f"file has more than {MAX_ROWS:,} rows; split it into smaller files")
        out = {h: (row.get(h) or "") for h in headers}
        sort_code, account = out[sc_col], out[acc_col]

        if damage := _excel_damage(sort_code, account):
            outcome, reason, clean_sc, clean_acc = NEEDS_REVIEW, damage, "", ""
        else:
            try:
                checked = check(sort_code, account, tables)
            except InvalidFormatError as exc:
                outcome, reason, clean_sc, clean_acc = (
                    BAD_FORMAT,
                    f"{str(exc).capitalize()}.",
                    "",
                    "",
                )
            else:
                outcome = checked.outcome.value
                reason = REASONS[checked.outcome]
                clean_sc = checked.details.formatted_sort_code
                clean_acc = checked.details.account_number

        out.update(
            sort_code_clean=clean_sc, account_number_clean=clean_acc, outcome=outcome, reason=reason
        )
        result.rows.append(out)
        result.summary[outcome] += 1
    return result
