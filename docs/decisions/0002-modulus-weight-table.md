# 0002. How to ship the Vocalink modulus weight table

- Status: Open question — decide before implementing the modulus check
- Date: 2026-11-25

## Context
Modulus checking needs Vocalink's weight table (`valacdos.txt`) and substitution
table (`scsubtab.txt`). Vocalink updates them a few times a year.

## Options
- **Bundle the files in the package.** Works offline; needs a release per Vocalink update,
  and the licence must allow redistribution. **Check the licence first.**
- **Download at runtime and cache.** Always current; needs network access and a pinned URL.
- **Let the caller pass a file path.** Simplest and licence-safe; worse first-run experience.

## Decision
Not made yet.
