# 0002. Download the Vocalink tables instead of bundling them

- Status: Proposed
- Date: 2026-11-25

## Context
Modulus checking needs Vocalink's weight table (`valacdos.txt`) and substitution table
(`scsubtab.txt`). Vocalink updates them several times a year. The spec is marked
"© Vocalink Limited, all rights reserved", and Pay.UK's website terms say publications
can't be redistributed through another website without written consent. I couldn't find
terms that clearly allow bundling the files in a public package.

## Decision
Don't ship the files. Instead:
- `python -m ukbankcheck download` reads Vocalink's modulus checking page, finds the
  current file links (their URLs change every release), downloads both files, **parses
  them before saving**, and writes them atomically. A bad download never replaces a good copy.
- `check()` loads tables from a cache directory (or a directory you pass), once per process.
- CI downloads the real files on every run and runs Vocalink's 34 published test cases.

## Alternatives considered
- **Bundle the files.** Best first-run experience and works offline, but possibly not
  allowed, and every Vocalink update would need a new release.
- **Hard-code the file URLs.** Simpler, but they change with each release, so it would
  break within months.
- **Caller always passes a path.** Licence-safe but leaves every user to write a downloader.

## Consequences
- First use needs one download (and network access).
- If Vocalink changes their page layout, `download` and CI fail loudly. That's intended:
  better than silently checking against stale rules.
- Revisit if Vocalink or Pay.UK confirm redistribution is allowed.
