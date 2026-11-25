import urllib.error
from pathlib import Path

import pytest

from ukbankcheck import __main__ as cli

W = "   2    1    2    1    2    1    2    1    2    1    2    1    2    1"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    (tmp_path / "valacdos.txt").write_text(f"499273 499273 DBLAL {W}\n")
    (tmp_path / "scsubtab.txt").write_text("")
    return tmp_path


def test_valid_exits_0(data_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["check", "49-92-73", "12345678", "--data-dir", str(data_dir)]) == 0
    assert "49-92-73 12345678: valid" in capsys.readouterr().out


def test_invalid_exits_1(data_dir: Path) -> None:
    assert cli.main(["check", "499273", "12345679", "--data-dir", str(data_dir)]) == 1


def test_bad_input_exits_2(data_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["check", "4992", "12345678", "--data-dir", str(data_dir)]) == 2
    assert "error:" in capsys.readouterr().err


def test_download_reports_where_it_saved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "download_tables", lambda dest: tmp_path)
    assert cli.main(["download"]) == 0
    assert str(tmp_path) in capsys.readouterr().out


def test_download_certificate_error_gives_a_hint(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(dest: object) -> Path:
        raise urllib.error.URLError("CERTIFICATE_VERIFY_FAILED")

    monkeypatch.setattr(cli, "download_tables", fail)
    assert cli.main(["download"]) == 2
    assert "Install Certificates" in capsys.readouterr().err
