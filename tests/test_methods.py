"""The two worked examples from the spec (sections 1.3.3 and 1.3.4), on hand-built rules.

These need no downloaded data: each builds a one-row table with the example's weights.
"""

from ukbankcheck import Method, ModulusTables, Outcome, WeightRule, check

DBLAL_WEIGHTS = (2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1)
MOD11_WEIGHTS = (0, 0, 0, 0, 0, 0, 7, 5, 8, 3, 4, 6, 2, 1)


def _table(sort_code: int, method: Method, weights: tuple[int, ...]) -> ModulusTables:
    return ModulusTables(rules=(WeightRule(sort_code, sort_code, method, weights),))


def test_double_alternate_worked_example() -> None:
    # 4 9 9 2 7 3 1 2 3 4 5 6 7 8 -> digit total 70, divisible by 10.
    tables = _table(499273, Method.DBLAL, DBLAL_WEIGHTS)
    assert check("499273", "12345678", tables).outcome is Outcome.VALID
    assert check("499273", "12345679", tables).outcome is Outcome.INVALID


def test_standard_modulus_11_worked_example() -> None:
    # 0 0 0 0 0 0 5 8 1 7 7 6 3 2 -> total 176, divisible by 11.
    tables = _table(0, Method.MOD11, MOD11_WEIGHTS)
    assert check("000000", "58177632", tables).outcome is Outcome.VALID


def test_modulus_10() -> None:
    tables = _table(0, Method.MOD10, (0,) * 13 + (1,))
    assert check("000000", "00000010", tables).valid
    assert not check("000000", "00000011", tables).valid


def test_sort_code_outside_every_range_is_not_checked() -> None:
    tables = _table(499273, Method.DBLAL, DBLAL_WEIGHTS)
    result = check("111111", "12345678", tables)
    assert result.outcome is Outcome.NOT_CHECKED
    assert result.valid  # presumed valid, as the spec says


def test_check_formats_input_first() -> None:
    tables = _table(499273, Method.DBLAL, DBLAL_WEIGHTS)
    assert check("49-92-73", "1234 5678", tables).details.formatted_sort_code == "49-92-73"
