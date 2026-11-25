# ukbankcheck

**Catch mistyped UK bank details before a payment fails.** A typed, dependency-free Python
library that validates sort codes and account numbers using Vocalink's modulus-checking rules.

[![CI](https://github.com/Itsraza099/ukbankcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Itsraza099/ukbankcheck/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ukbankcheck)](https://pypi.org/project/ukbankcheck/)
![Python](https://img.shields.io/badge/python-3.10–3.13-blue)
![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)
![Licence](https://img.shields.io/badge/licence-MIT-lightgrey)

| | |
|---|---|
| **Problem** | A wrong digit in a sort code or account number means a failed Direct Debit, a fee and a chasing email. |
| **Solution** | Validate the details at entry time with the same algorithm UK banks publish. |
| **Shows** | Python packaging, semantic versioning, property-based testing, strict typing, CI/CD to PyPI |
| **Stack** | Python · uv · hatchling · pytest · Hypothesis · mypy --strict · ruff · GitHub Actions |

```bash
pip install ukbankcheck
python -m ukbankcheck download              # once: fetch Vocalink's latest tables
python -m ukbankcheck check 08-99-99 66374958
# 08-99-99 66374958: valid
```

```python
from ukbankcheck import check, Outcome

result = check("08-99-99", "66374959")  # one digit wrong
result.valid  # False
result.outcome  # Outcome.INVALID

check("12-34-56", "12345678").outcome  # Outcome.NOT_CHECKED: no rules for this sort code
```

## Engineering highlights

- **Verified against the official test suite.** All 34 of Vocalink's published test cases
  run in CI against freshly downloaded tables, covering every method and all 14 exceptions.
  ([tests/test_spec_cases.py](tests/test_spec_cases.py))
- **Found a contradiction in the spec.** The flowchart says exception 5 passes if *either*
  check passes; the test cases require *both*. I followed the tests, and a planted-bug run
  confirmed cases 23–25 catch the flowchart version.
  ([decision 0003](docs/decisions/0003-four-outcomes-not-a-boolean.md))
- **"Unknown" isn't "valid".** Results say whether a check actually ran (`NOT_CHECKED`,
  `FOREIGN_CURRENCY`) instead of collapsing everything into `True`.
- **Safe data updates.** Vocalink's tables are downloaded, parsed and validated (sorted, no
  overlapping ranges) *before* being written atomically, so a bad download can't replace a
  good copy. ([decision 0002](docs/decisions/0002-modulus-weight-table.md))
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
- [x] Table download with validation ([decision 0002](docs/decisions/0002-modulus-weight-table.md))
- [x] Standard, double alternate and all 14 exceptions; 34/34 spec cases pass
- [x] [`v0.1.0` on PyPI](https://pypi.org/project/ukbankcheck/)
- [ ] Batch checker in the browser: upload a CSV, get results back, data never leaves the page ([decision 0004](docs/decisions/0004-in-browser-batch-checker.md))
- [ ] Nine- and ten-digit account numbers (bank-specific conversions)

## How I worked

New to modulus checking? Start with [how it works](docs/how-modulus-checking-works.md).
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
make tables    # download Vocalink's tables into .vocalink/ (gitignored)
make check     # ruff, mypy --strict, pytest with coverage
```
</details>
