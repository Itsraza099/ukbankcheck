# 0003. Return four outcomes, not just valid/invalid

- Status: Proposed
- Date: 2026-11-25

## Context
The spec says two different things are "presumed valid": a sort code with no modulus
rules, and an exception-6 foreign currency account. In both cases nothing was actually
checked. A plain `True` would hide that from callers.

## Decision
`check()` returns a `CheckResult` with an `outcome`:

| Outcome | Meaning | `.valid` |
|---|---|---|
| `VALID` | Checks ran and passed | True |
| `INVALID` | A check ran and failed | False |
| `NOT_CHECKED` | Sort code has no modulus rules | True |
| `FOREIGN_CURRENCY` | Exception 6: can't be checked | True |

`.valid` follows the spec for simple callers; `outcome` lets careful callers (like a data
migration) report how many records were genuinely verified.

## Alternatives considered
- Return `bool`: simplest, but "unknown" and "verified" look identical.
- Raise an exception for unchecked codes: forces callers to handle a normal situation as an error.

## Spec conflict found while building
The spec's flowchart lists exception 5 among those where passing *either* check is enough,
but its test cases 23–25 require *both* checks to pass. I followed the test cases; a test
proves that switching to the flowchart's rule breaks cases 23–25.
