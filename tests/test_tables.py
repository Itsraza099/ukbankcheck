from pathlib import Path

import pytest

from ukbankcheck import Method, ModulusTables, TableFormatError, TablesNotFoundError, load_tables
from ukbankcheck._tables import default_data_dir, parse_substitutions, parse_weights

W = "   0    0    0    0    0    0    8    7    6    5    4    3    2    1"
LINES = [
    f"010004 016715 MOD11 {W}",
    f"200000 200002 MOD11 {W}   6",
    f"200000 200002 DBLAL {W}   6",
    "",
]


def test_parses_rows_and_exceptions() -> None:
    rules = parse_weights(LINES)
    assert len(rules) == 3
    assert rules[0].method is Method.MOD11 and rules[0].exception is None
    assert rules[2].method is Method.DBLAL and rules[2].exception == 6
    assert rules[0].weights == (0, 0, 0, 0, 0, 0, 8, 7, 6, 5, 4, 3, 2, 1)


def test_lookup_is_inclusive_at_both_ends_and_returns_both_rows() -> None:
    tables = ModulusTables(parse_weights(LINES))
    assert len(tables.rules_for("010004")) == 1
    assert len(tables.rules_for("016715")) == 1
    assert len(tables.rules_for("200001")) == 2
    assert tables.rules_for("010003") == []
    assert tables.rules_for("016716") == []
    assert tables.rules_for("000001") == []


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (f"010004 016715 MOD12 {W}", "MOD12"),
        ("010004 016715 MOD11 1 2 3", "17 or 18 fields"),
        (f"016715 010004 MOD11 {W}", "after end"),
    ],
)
def test_bad_lines_are_rejected_with_line_number(line: str, message: str) -> None:
    with pytest.raises(TableFormatError, match=message):
        parse_weights([line])


def test_empty_table_is_rejected() -> None:
    with pytest.raises(TableFormatError, match="empty"):
        parse_weights(["", "  "])


def test_overlapping_ranges_are_rejected() -> None:
    rules = parse_weights([f"010000 010010 MOD11 {W}", f"010005 010020 MOD11 {W}"])
    with pytest.raises(TableFormatError, match="overlaps"):
        ModulusTables(rules)


def test_out_of_order_rows_are_rejected() -> None:
    rules = parse_weights([f"020000 020010 MOD11 {W}", f"010000 010010 MOD11 {W}"])
    with pytest.raises(TableFormatError, match="out of order"):
        ModulusTables(rules)


def test_substitutions() -> None:
    assert parse_substitutions(["938173 938017", ""]) == {"938173": "938017"}
    with pytest.raises(TableFormatError):
        parse_substitutions(["938173"])


def test_missing_files_give_a_helpful_error(tmp_path: Path) -> None:
    with pytest.raises(TablesNotFoundError, match="ukbankcheck download"):
        load_tables(tmp_path)


def test_data_dir_follows_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UKBANKCHECK_DATA_DIR", str(tmp_path))
    assert default_data_dir() == tmp_path
    monkeypatch.delenv("UKBANKCHECK_DATA_DIR")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert default_data_dir() == tmp_path / "ukbankcheck"
