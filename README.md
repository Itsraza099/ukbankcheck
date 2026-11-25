# ukbankcheck

**Catch mistyped UK bank details before a payment fails.** A typed, dependency-free Python
library that validates sort codes and account numbers using Vocalink's modulus-checking rules.

[![CI](https://github.com/Itsraza099/ukbankcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Itsraza099/ukbankcheck/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10–3.13-blue)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Licence](https://img.shields.io/badge/licence-MIT-lightgrey)

| | |
|---|---|
| **Problem** | A wrong digit in a sort code or account number means a failed Direct Debit, a fee and a chasing email. |
| **Solution** | Validate the details at entry time with the same algorithm UK banks publish. |
| **Shows** | Python packaging, semantic versioning, property-based testing, strict typing, CI/CD to PyPI |
| **Stack** | Python · uv · hatchling · pytest · Hypothesis · mypy --strict · ruff · GitHub Actions |

```python
from ukbankcheck import normalise, is_well_formed

normalise("12-34-56", "123456")
# BankDetails(sort_code='123456', account_number='00123456')

is_well_formed("12 34 5", "12345678")   # False: only five sort-code digits
```

## Engineering highlights

- **Property-based tests.** Alongside normal examples, Hypothesis generates hundreds of random
  inputs per run to prove rules like "formatting never changes the result" and "normalising
  twice equals normalising once". ([tests/test_properties.py](tests/test_properties.py))
- **Caught a real edge case.** `"١٢٣٤٥٦"` (Arabic-Indic digits) passes Python's `str.isdigit()`;
  the library rejects it explicitly.
- **Tested on four Python versions** in CI, with a 90% coverage gate (currently 100%).
- **Token-free releases.** Tagging `v*` publishes to PyPI through trusted publishing, so no
  long-lived API key is stored anywhere. ([decision 0001](docs/decisions/0001-packaging-and-tooling.md))

## Build progress

- [x] Input normalisation and shape checks
- [x] CI on Python 3.10–3.13, release workflow
- [ ] Vocalink weight table loading ([open decision](docs/decisions/0002-modulus-weight-table.md))
- [ ] Standard, double-alternate and exception modulus checks
- [ ] `v0.1.0` on PyPI

## How I worked

Every design choice has a short [decision record](docs/decisions/) covering the options
considered and why one won. The [glossary](docs/glossary.md) is my own explanation of each
concept, with examples from this code.

**Part of a portfolio:** this library is used by
[migration-toolkit](https://github.com/Itsraza099/migration-toolkit) to flag bad bank details
during a CRM migration. See all projects on [my profile](https://github.com/Itsraza099).

<details>
<summary><b>Run locally</b></summary>

Needs [uv](https://docs.astral.sh/uv/).

```bash
make install   # create .venv and install dev tools
make check     # ruff, mypy --strict, pytest with coverage
```
</details>
