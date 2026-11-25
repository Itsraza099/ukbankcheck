"""Validate UK sort codes and account numbers with Vocalink modulus checking."""

from ukbankcheck._download import download_tables
from ukbankcheck._modulus import CheckResult, Outcome, check
from ukbankcheck._normalise import BankDetails, InvalidFormatError, is_well_formed, normalise
from ukbankcheck._tables import (
    Method,
    ModulusTables,
    TableFormatError,
    TablesNotFoundError,
    WeightRule,
    load_tables,
)

__all__ = [
    "BankDetails",
    "CheckResult",
    "InvalidFormatError",
    "Method",
    "ModulusTables",
    "Outcome",
    "TableFormatError",
    "TablesNotFoundError",
    "WeightRule",
    "check",
    "download_tables",
    "is_well_formed",
    "load_tables",
    "normalise",
]
__version__ = "0.1.0.dev0"
