"""The downloader, with the network replaced by a fake so tests are fast and offline."""

from pathlib import Path

import pytest

from ukbankcheck import TableFormatError, download_tables, load_tables
from ukbankcheck._download import PAGE_URL, find_file_urls

W = "   0    0    0    0    0    0    8    7    6    5    4    3    2    1"
PAGE = '<a href="/media/abc/valacdos.txt">w</a> <a href="/media/def/scsubtab.txt">s</a>'
GOOD = {
    PAGE_URL: PAGE.encode(),
    "https://www.vocalink.com/media/abc/valacdos.txt": f"010004 016715 MOD11 {W}\r\n".encode(),
    "https://www.vocalink.com/media/def/scsubtab.txt": b"938173 938017\r\n",
}


def test_links_are_resolved_against_the_page() -> None:
    urls = find_file_urls(PAGE)
    assert urls["valacdos.txt"] == "https://www.vocalink.com/media/abc/valacdos.txt"


def test_missing_link_is_an_error() -> None:
    with pytest.raises(RuntimeError, match=r"scsubtab\.txt"):
        find_file_urls('<a href="/x/valacdos.txt">')


def test_download_saves_loadable_tables(tmp_path: Path) -> None:
    download_tables(tmp_path, fetch=GOOD.__getitem__)
    assert len(load_tables(tmp_path).rules) == 1


def test_bad_download_never_replaces_good_files(tmp_path: Path) -> None:
    download_tables(tmp_path, fetch=GOOD.__getitem__)
    before = (tmp_path / "valacdos.txt").read_bytes()

    corrupt = dict(GOOD)
    corrupt["https://www.vocalink.com/media/abc/valacdos.txt"] = b"<html>error page</html>"
    with pytest.raises(TableFormatError):
        download_tables(tmp_path, fetch=corrupt.__getitem__)

    assert (tmp_path / "valacdos.txt").read_bytes() == before
