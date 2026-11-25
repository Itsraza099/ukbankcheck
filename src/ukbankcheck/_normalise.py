"""Turn user-typed bank details into a canonical form before any modulus check runs.

People type sort codes as ``12-34-56``, ``12 34 56`` or ``123456``. The modulus
algorithm needs exactly six sort-code digits and eight account digits, so every
input goes through :func:`normalise` first.
"""

from __future__ import annotations

from dataclasses import dataclass

_SEPARATORS = str.maketrans("", "", " -")
SORT_CODE_LENGTH = 6
ACCOUNT_LENGTH = 8
# Vocalink's rule: shorter account numbers are left-padded with zeros to eight digits.
# Nine- and ten-digit accounts need bank-specific handling and are not supported yet.
MIN_ACCOUNT_LENGTH = 6


class InvalidFormatError(ValueError):
    """Raised when input can't be a UK sort code or account number."""


@dataclass(frozen=True)
class BankDetails:
    """A sort code and account number in canonical form (digits only, fixed length)."""

    sort_code: str
    account_number: str

    @property
    def formatted_sort_code(self) -> str:
        """The sort code as people usually write it, e.g. ``12-34-56``."""
        s = self.sort_code
        return f"{s[0:2]}-{s[2:4]}-{s[4:6]}"


def _digits_only(value: str, field: str) -> str:
    cleaned = value.strip().translate(_SEPARATORS)
    if not cleaned.isascii() or not cleaned.isdigit():
        raise InvalidFormatError(f"{field} must contain only digits, spaces or hyphens")
    return cleaned


def normalise(sort_code: str, account_number: str) -> BankDetails:
    """Return canonical bank details, or raise :class:`InvalidFormatError`."""
    sc = _digits_only(sort_code, "sort code")
    if len(sc) != SORT_CODE_LENGTH:
        raise InvalidFormatError(f"sort code must have {SORT_CODE_LENGTH} digits, got {len(sc)}")

    acc = _digits_only(account_number, "account number")
    if not MIN_ACCOUNT_LENGTH <= len(acc) <= ACCOUNT_LENGTH:
        raise InvalidFormatError(
            f"account number must have {MIN_ACCOUNT_LENGTH}-{ACCOUNT_LENGTH} digits, got {len(acc)}"
        )
    return BankDetails(sort_code=sc, account_number=acc.zfill(ACCOUNT_LENGTH))


def is_well_formed(sort_code: str, account_number: str) -> bool:
    """True if the details have a valid shape. This is *not* a modulus check."""
    try:
        normalise(sort_code, account_number)
    except InvalidFormatError:
        return False
    return True
