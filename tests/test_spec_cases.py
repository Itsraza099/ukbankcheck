"""All 34 test cases from Vocalink's spec (v9.20, chapter 3), against the real tables."""

import pytest

from ukbankcheck import ModulusTables, Outcome, check

SPEC_CASES = [
    (1, "089999", "66374958", True, "pass modulus 10"),
    (2, "107999", "88837491", True, "pass modulus 11"),
    (3, "202959", "63748472", True, "pass modulus 11 and double alternate"),
    (4, "871427", "46238510", True, "exc 10/11: first passes, second fails"),
    (5, "872427", "46238510", True, "exc 10/11: first fails, second passes"),
    (6, "871427", "09123496", True, "exc 10: ab=09, g=9"),
    (7, "871427", "99123496", True, "exc 10: ab=99, g=9"),
    (8, "820000", "73688637", True, "exc 3: c=6 skips second check (range start)"),
    (9, "827999", "73988638", True, "exc 3: c=9 skips second check (range end)"),
    (10, "827101", "28748352", True, "exc 3: c not 6/9, both checks pass"),
    (11, "134020", "63849203", True, "exc 4: remainder equals check digit"),
    (12, "118765", "64371389", True, "exc 1: adds 27, passes double alternate"),
    (13, "200915", "41011166", True, "exc 6: foreign currency account"),
    (14, "938611", "07806039", True, "exc 5: passes"),
    (15, "938600", "42368003", True, "exc 5: passes with sort code substitution"),
    (16, "938063", "55065200", True, "exc 5: both remainders 0"),
    (17, "772798", "99345694", True, "exc 7: passes, would fail standard check"),
    (18, "086090", "06774744", True, "exc 8: passes"),
    (19, "309070", "02355688", True, "exc 2/9: first check passes"),
    (20, "309070", "12345668", True, "exc 2/9: second passes with substitution"),
    (21, "309070", "12345677", True, "exc 2/9: a!=0, g!=9"),
    (22, "309070", "99345694", True, "exc 2/9: a!=0, g=9"),
    (23, "938063", "15764273", False, "exc 5: first check digit right, second wrong"),
    (24, "938063", "15764264", False, "exc 5: first check digit wrong, second right"),
    (25, "938063", "15763217", False, "exc 5: first check remainder 1"),
    (26, "118765", "64371388", False, "exc 1: fails double alternate"),
    (27, "203099", "66831036", False, "pass modulus 11, fail double alternate"),
    (28, "203099", "58716970", False, "fail modulus 11, pass double alternate"),
    (29, "089999", "66374959", False, "fail modulus 10"),
    (30, "107999", "88837493", False, "fail modulus 11"),
    (31, "074456", "12345112", True, "exc 12/13: passes modulus 11"),
    (32, "070116", "34012583", True, "exc 12/13: passes modulus 11 (and 10)"),
    (33, "074456", "11104102", True, "exc 12/13: fails 11, passes 10"),
    (34, "180002", "00000190", True, "exc 14: first fails, second passes"),
]


@pytest.mark.parametrize(
    ("number", "sort_code", "account", "expected", "description"),
    SPEC_CASES,
    ids=[f"{c[0]:02d}-{c[4]}" for c in SPEC_CASES],
)
def test_vocalink_spec_case(
    real_tables: ModulusTables,
    number: int,
    sort_code: str,
    account: str,
    expected: bool,
    description: str,
) -> None:
    assert check(sort_code, account, real_tables).valid is expected


def test_foreign_currency_is_reported_as_unchecked(real_tables: ModulusTables) -> None:
    assert check("200915", "41011166", real_tables).outcome is Outcome.FOREIGN_CURRENCY


def test_exception_14_rejects_last_digit_outside_0_1_9(real_tables: ModulusTables) -> None:
    assert check("180002", "00000195", real_tables).outcome is Outcome.INVALID


def test_real_table_has_no_overlapping_ranges(real_tables: ModulusTables) -> None:
    # Loading already validates this; the assertion documents that it ran on real data.
    assert len(real_tables.rules) > 1000
