"""Example-based unit tests: one known input, one expected output."""

import pytest

from ukbankcheck import BankDetails, InvalidFormatError, is_well_formed, normalise


@pytest.mark.parametrize("sort_code", ["12-34-56", "12 34 56", "123456", " 123456 "])
def test_sort_code_separators_are_removed(sort_code: str) -> None:
    assert normalise(sort_code, "12345678").sort_code == "123456"


def test_short_account_numbers_are_zero_padded() -> None:
    assert normalise("123456", "123456").account_number == "00123456"
    assert normalise("123456", "1234567").account_number == "01234567"


def test_formatted_sort_code() -> None:
    assert BankDetails("123456", "12345678").formatted_sort_code == "12-34-56"


@pytest.mark.parametrize(
    ("sort_code", "account_number", "message"),
    [
        ("12345", "12345678", "6 digits"),
        ("1234567", "12345678", "6 digits"),
        ("12a456", "12345678", "only digits"),
        ("123456", "12345", "6-8 digits"),
        ("123456", "123456789", "6-8 digits"),
        ("١٢٣٤٥٦", "12345678", "only digits"),  # Arabic-Indic digits pass str.isdigit()
    ],
)
def test_bad_input_is_rejected(sort_code: str, account_number: str, message: str) -> None:
    with pytest.raises(InvalidFormatError, match=message):
        normalise(sort_code, account_number)


def test_is_well_formed() -> None:
    assert is_well_formed("12-34-56", "12345678")
    assert not is_well_formed("12-34-5", "12345678")
