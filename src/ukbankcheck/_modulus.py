"""Vocalink modulus checking (spec v9.20, "Validating account numbers: UK modulus checking").

Digits are named as in the spec:

    sort code:      u v w x y z        (positions 0-5)
    account number: a b c d e f g h    (positions 6-13)

A *valid* result means the account number is possible for that sort code, not that the
account exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

from ukbankcheck._normalise import BankDetails, normalise
from ukbankcheck._tables import (
    Method,
    ModulusTables,
    WeightRule,
    default_data_dir,
    load_tables,
)

# Exception 2: replacement weights for Lloyds euro accounts (section 2.2.2.2).
_EX2_WEIGHTS = (0, 0, 1, 2, 5, 3, 6, 4, 8, 7, 10, 9, 3, 1)
_EX2_WEIGHTS_G9 = (0, 0, 0, 0, 0, 0, 0, 0, 8, 7, 10, 9, 3, 1)
_EX8_SORT_CODE = "090126"
_EX9_SORT_CODE = "309634"
_A, _B, _C, _G, _H = 6, 7, 8, 12, 13  # digit positions in the 14-digit string


class Outcome(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    NOT_CHECKED = "not_checked"  # sort code has no modulus rules: presumed valid
    FOREIGN_CURRENCY = "foreign_currency"  # exception 6: can't be checked: presumed valid


@dataclass(frozen=True)
class CheckResult:
    details: BankDetails
    outcome: Outcome

    @property
    def valid(self) -> bool:
        """False only when a check ran and failed. Unknown is not the same as wrong."""
        return self.outcome is not Outcome.INVALID


def _digit_sum(n: int) -> int:
    return sum(int(c) for c in str(abs(n)))


def _passes(rule: WeightRule, sort_code: str, account: str, tables: ModulusTables) -> bool:
    """Run one row of the weight table, applying that row's exception."""
    ex = rule.exception
    if ex == 5:
        sort_code = tables.substitutions.get(sort_code, sort_code)
    elif ex == 8:
        sort_code = _EX8_SORT_CODE
    elif ex == 9:
        sort_code = _EX9_SORT_CODE

    digits = [int(c) for c in sort_code + account]
    weights = list(rule.weights)
    if ex == 2 and digits[_A] != 0:
        weights = list(_EX2_WEIGHTS_G9 if digits[_G] == 9 else _EX2_WEIGHTS)
    zeroise_u_to_b = (ex == 7 and digits[_G] == 9) or (
        ex == 10 and account[:2] in ("09", "99") and digits[_G] == 9
    )
    if zeroise_u_to_b:
        weights[: _B + 1] = [0] * (_B + 1)

    products = [d * w for d, w in zip(digits, weights, strict=True)]

    if rule.method is Method.DBLAL:
        total = sum(_digit_sum(p) for p in products) + (27 if ex == 1 else 0)
        if ex == 5:  # the remainder must produce the check digit h
            remainder = total % 10
            return (10 - remainder) % 10 == digits[_H]
        return total % 10 == 0

    total = sum(products)
    if ex == 4:  # the remainder must equal the two-digit check digit gh
        return total % 11 == int(account[6:8])
    if ex == 5:  # the remainder must produce the check digit g
        remainder = total % 11
        if remainder == 1:
            return False
        return (11 - remainder) % 11 == digits[_G]
    modulus = 10 if rule.method is Method.MOD10 else 11
    return total % modulus == 0


def _evaluate(details: BankDetails, tables: ModulusTables) -> Outcome:
    sort_code, account = details.sort_code, details.account_number
    rules = tables.rules_for(sort_code)
    if not rules:
        return Outcome.NOT_CHECKED

    first = rules[0]
    second = rules[1] if len(rules) > 1 else None
    exceptions = {r.exception for r in rules}

    # Exception 6: foreign currency accounts can't be checked.
    if 6 in exceptions and account[0] in "45678" and account[6] == account[7]:
        return Outcome.FOREIGN_CURRENCY

    first_ok = _passes(first, sort_code, account, tables)

    if first.exception == 14 and not first_ok:
        # Exception 14 (Coutts): retry without the last digit if it's 0, 1 or 9.
        if account[7] not in "019":
            return Outcome.INVALID
        first_ok = _passes(first, sort_code, "0" + account[:7], tables)

    if second is None:
        return Outcome.VALID if first_ok else Outcome.INVALID

    # Exceptions 2/9, 10/11 and 12/13: passing either check is enough.
    if first.exception in (2, 10, 12):
        ok = first_ok or _passes(second, sort_code, account, tables)
        return Outcome.VALID if ok else Outcome.INVALID

    # Exception 3: skip the second (double alternate) check when c is 6 or 9.
    if second.exception == 3 and account[2] in "69":
        return Outcome.VALID if first_ok else Outcome.INVALID

    # Otherwise (including exception 5) both checks must pass.
    ok = first_ok and _passes(second, sort_code, account, tables)
    return Outcome.VALID if ok else Outcome.INVALID


def check(sort_code: str, account_number: str, tables: ModulusTables | None = None) -> CheckResult:
    """Modulus check a UK sort code and account number.

    Raises :class:`~ukbankcheck.InvalidFormatError` if the input can't be a sort code or
    account number, and :class:`~ukbankcheck.TablesNotFoundError` if no tables are given
    and none have been downloaded.
    """
    details = normalise(sort_code, account_number)
    return CheckResult(details, _evaluate(details, tables or _cached_tables(default_data_dir())))


@lru_cache(maxsize=4)
def _cached_tables(directory: Path) -> ModulusTables:
    """Parse the files once per process, not once per check."""
    return load_tables(directory)
