# Changelog

All notable changes are listed here. This project follows
[Semantic Versioning](https://semver.org/): MAJOR for breaking API changes,
MINOR for new features, PATCH for fixes.

## [Unreleased]

### Added
- `check()`: full Vocalink modulus checking (spec v9.20): standard 10/11, double alternate
  and exceptions 1–14. Passes all 34 of Vocalink's published test cases.
- `CheckResult.outcome`: `VALID`, `INVALID`, `NOT_CHECKED` or `FOREIGN_CURRENCY`.
- `python -m ukbankcheck download`: fetches and validates the latest Vocalink tables.
- `python -m ukbankcheck check SORT_CODE ACCOUNT`: command-line check (exit code 1 if invalid).
- `normalise()` and `is_well_formed()` for sort code and account number input.
