"""Command line: `python -m ukbankcheck download` and `python -m ukbankcheck check SC ACC`."""

from __future__ import annotations

import argparse
import sys
import urllib.error
from collections.abc import Sequence
from pathlib import Path

from ukbankcheck._download import download_tables
from ukbankcheck._modulus import check
from ukbankcheck._normalise import InvalidFormatError
from ukbankcheck._tables import TablesNotFoundError, load_tables
from ukbankcheck.batch import OUTCOME_ORDER, BatchError, check_rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ukbankcheck")
    sub = parser.add_subparsers(dest="command", required=True)

    dl = sub.add_parser("download", help="download the latest Vocalink tables")
    dl.add_argument("--dest", type=Path, help="directory to save into")

    ck = sub.add_parser("check", help="modulus check a sort code and account number")
    ck.add_argument("sort_code")
    ck.add_argument("account_number")
    ck.add_argument("--data-dir", type=Path, help="directory holding the tables")

    cf = sub.add_parser("check-file", help="check every row of a CSV file")
    cf.add_argument("input", type=Path, help="CSV with sort code and account number columns")
    cf.add_argument("-o", "--output", type=Path, help="where to write results (default: stdout)")
    cf.add_argument("--data-dir", type=Path, help="directory holding the tables")

    args = parser.parse_args(argv)

    if args.command == "download":
        try:
            path = download_tables(args.dest)
        except urllib.error.URLError as exc:
            print(f"error: download failed: {exc.reason}", file=sys.stderr)
            if "CERTIFICATE_VERIFY_FAILED" in str(exc.reason):
                print(
                    "hint: on macOS with python.org Python, run "
                    "'Install Certificates.command' from the Python folder in Applications.",
                    file=sys.stderr,
                )
            return 2
        print(f"Saved Vocalink tables to {path}")
        return 0

    if args.command == "check-file":
        return _check_file(args.input, args.output, args.data_dir)

    try:
        tables = load_tables(args.data_dir) if args.data_dir else None
        result = check(args.sort_code, args.account_number, tables)
    except (InvalidFormatError, TablesNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        f"{result.details.formatted_sort_code} {result.details.account_number}: "
        f"{result.outcome.value}"
    )
    return 0 if result.valid else 1


def _check_file(source: Path, output: Path | None, data_dir: Path | None) -> int:
    try:
        result = check_rows(source.read_text(encoding="utf-8-sig"), load_tables(data_dir))
    except (BatchError, TablesNotFoundError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if output:
        output.write_text(result.to_csv(), encoding="utf-8")
    else:
        sys.stdout.write(result.to_csv())
    summary = ", ".join(f"{result.summary[o]} {o}" for o in OUTCOME_ORDER if result.summary[o])
    print(f"{len(result.rows)} rows: {summary or 'none'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
