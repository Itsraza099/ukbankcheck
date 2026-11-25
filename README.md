# ukbankcheck

[![CI](https://github.com/Itsraza099/ukbankcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Itsraza099/ukbankcheck/actions/workflows/ci.yml)

Validate UK sort codes and account numbers in Python, using Vocalink's modulus-checking rules.
Typed, dependency-free, and tested with both example-based and property-based tests.

> **Status:** early development. Input normalisation works; the modulus check itself is next.

```python
from ukbankcheck import normalise, is_well_formed

normalise("12-34-56", "123456")
# BankDetails(sort_code='123456', account_number='00123456')

is_well_formed("12 34 5", "12345678")  # False: only five sort-code digits
```

## Why this exists

A modulus check catches typos in bank details *before* a payment is attempted, which is
cheaper than a failed Direct Debit. It is also used by
[migration-toolkit](https://github.com/Itsraza099/migration-toolkit) to flag bad bank
details while migrating legacy CRM records.

## Roadmap

- [x] Normalise and shape-check input
- [ ] Load the Vocalink weight table ([decision 0002](docs/decisions/0002-modulus-weight-table.md))
- [ ] Standard, double-alternate and exception modulus checks → `check()`
- [ ] First release to PyPI (`v0.1.0`)

## Development

Needs [uv](https://docs.astral.sh/uv/).

```bash
make install   # create .venv and install dev tools
make check     # ruff, mypy --strict, pytest with coverage
```

## Learning notes

- [Decision records](docs/decisions/) – why it's built this way
- [Glossary](docs/glossary.md) – packaging, semver, property-based tests, CI/CD…
- [Interview check](docs/interview-check.md)

## Licence

MIT
