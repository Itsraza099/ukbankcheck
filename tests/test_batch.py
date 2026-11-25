"""Batch checking, on a small hand-built table so no downloaded data is needed."""

from pathlib import Path

import pytest

from ukbankcheck import ModulusTables
from ukbankcheck import __main__ as cli
from ukbankcheck.batch import BatchError, check_rows

W_DBLAL = " ".join(["2", "1"] * 7)
TABLES = ModulusTables.from_text(f"499273 499273 DBLAL {W_DBLAL}\n")


def test_outcomes_and_passthrough_columns() -> None:
    csv_text = (
        "Customer,Sort Code,Account Number\n"
        "Acme,49-92-73,12345678\n"  # valid (spec worked example)
        "Beta,49-92-73,12345679\n"  # invalid
        "Gamma,11-11-11,12345678\n"  # no rules for this sort code
        "Delta,49927,12345678\n"  # Excel ate the leading zero
        "Echo,4992,12345678\n"  # too short to be a sort code
        ",,\n"  # blank row: skipped
    )
    result = check_rows(csv_text, TABLES)
    outcomes = [r["outcome"] for r in result.rows]
    assert outcomes == ["valid", "invalid", "not_checked", "needs_review", "bad_format"]
    assert result.rows[0]["Customer"] == "Acme"
    assert result.rows[0]["sort_code_clean"] == "49-92-73"
    assert result.summary["valid"] == 1
    assert result.columns[:3] == ["Customer", "Sort Code", "Account Number"]


def test_scientific_notation_is_flagged() -> None:
    result = check_rows("sort_code,account_number\n499273,1.23457E+07\n", TABLES)
    assert result.rows[0]["outcome"] == "needs_review"
    assert "scientific" in result.rows[0]["reason"]


def test_csv_round_trip_keeps_columns_in_order() -> None:
    result = check_rows("﻿sort_code,account_number\n499273,12345678\n", TABLES)
    lines = result.to_csv().splitlines()
    assert (
        lines[0] == "sort_code,account_number,sort_code_clean,account_number_clean,outcome,reason"
    )
    assert ",valid," in lines[1]


@pytest.mark.parametrize(
    ("header", "missing"),
    [("account_number\n", "sort code"), ("sort_code,name\n", "account number"), ("", "sort code")],
)
def test_missing_columns_are_explained(header: str, missing: str) -> None:
    with pytest.raises(BatchError, match=f"no {missing} column"):
        check_rows(header, TABLES)


def test_row_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ukbankcheck.batch.MAX_ROWS", 1)
    with pytest.raises(BatchError, match="more than 1 rows"):
        check_rows("sort_code,account_number\n499273,1\n499273,2\n", TABLES)


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    (tmp_path / "valacdos.txt").write_text(f"499273 499273 DBLAL {W_DBLAL}\n")
    (tmp_path / "scsubtab.txt").write_text("")
    return tmp_path


def test_check_file_writes_output(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src, out = tmp_path / "in.csv", tmp_path / "out.csv"
    src.write_text("sort_code,account_number\n49-92-73,12345678\n49-92-73,12345679\n")
    assert cli.main(["check-file", str(src), "-o", str(out), "--data-dir", str(data_dir)]) == 0
    assert out.read_text().count(",valid,") == 1
    assert "2 rows: 1 valid, 1 invalid" in capsys.readouterr().err


def test_check_file_to_stdout(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "in.csv"
    src.write_text("sort_code,account_number\n")
    assert cli.main(["check-file", str(src), "--data-dir", str(data_dir)]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("sort_code,account_number,")
    assert "0 rows: none" in captured.err


def test_check_file_reports_bad_input(data_dir: Path, tmp_path: Path) -> None:
    src = tmp_path / "in.csv"
    src.write_text("name\nx\n")
    assert cli.main(["check-file", str(src), "--data-dir", str(data_dir)]) == 2
