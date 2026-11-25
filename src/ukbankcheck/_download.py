"""Download the latest Vocalink tables into a local directory.

Vocalink's file URLs change with each release, so the links are read from the modulus
checking page rather than hard-coded. Files are parsed *before* being saved, and written
atomically, so a bad or half-finished download never replaces a good copy.
"""

from __future__ import annotations

import os
import re
import tempfile
import urllib.request
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urljoin

from ukbankcheck._tables import (
    SUBSTITUTIONS_FILE,
    WEIGHTS_FILE,
    default_data_dir,
    parse_substitutions,
    parse_weights,
)

PAGE_URL = "https://www.vocalink.com/tools/modulus-checking/"
USER_AGENT = "ukbankcheck (+https://github.com/Itsraza099/ukbankcheck)"

Fetch = Callable[[str], bytes]


def _http_get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        body: bytes = response.read()
        return body


def find_file_urls(page_html: str, page_url: str = PAGE_URL) -> dict[str, str]:
    """Find the current valacdos.txt and scsubtab.txt links on Vocalink's page."""
    urls = {}
    for name in (WEIGHTS_FILE, SUBSTITUTIONS_FILE):
        match = re.search(rf'href="([^"]*{re.escape(name)})"', page_html, re.IGNORECASE)
        if not match:
            raise RuntimeError(f"couldn't find a link to {name} on {page_url}")
        urls[name] = urljoin(page_url, match.group(1))
    return urls


def _write_atomic(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def download_tables(dest: Path | None = None, fetch: Fetch = _http_get) -> Path:
    """Fetch, validate and save both tables. Returns the directory they were saved to."""
    dest = dest or default_data_dir()
    dest.mkdir(parents=True, exist_ok=True)
    urls = find_file_urls(fetch(PAGE_URL).decode("utf-8", errors="replace"))

    files = {name: fetch(url) for name, url in urls.items()}
    parse_weights(files[WEIGHTS_FILE].decode("ascii").splitlines())
    parse_substitutions(files[SUBSTITUTIONS_FILE].decode("ascii").splitlines())

    for name, data in files.items():
        _write_atomic(dest / name, data)
    return dest
