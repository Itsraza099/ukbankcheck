# How UK modulus checking works

**What problem it solves.** A typo in an account number usually makes it an impossible
number. Modulus checking spots that *before* a payment is sent, so it doesn't bounce days
later with a fee. It can't tell you an account exists, only that the number is possible.

**The idea.** Each bank builds a check digit into its account numbers. Multiply every digit
of sort code + account number (14 digits, named `u v w x y z a b c d e f g h`) by a weight,
add the results, and divide by 10 or 11. If there's no remainder, the number is possible.

```
sort code 000000, account 58177632, modulus 11

digits   0 0 0 0 0 0  5  8 1  7  7  6 3 2
weights  0 0 0 0 0 0  7  5 8  3  4  6 2 1
products 0 0 0 0 0 0 35 40 8 21 28 36 6 2   → total 176 → 176 / 11 = 16, remainder 0 ✓
```

**Three methods.**
- **Standard modulus 10 / 11:** add the products, divide by 10 or 11.
- **Double alternate:** add the *digits* of the products (14 becomes 1 + 4), divide by 10.

**Why it's fiddly.** Which method and weights apply depends on the sort code (about 1,200
ranges in Vocalink's table), and 14 numbered *exceptions* change the rules for particular
banks: substitute a different sort code, zero some weights, add 27 to the total, accept if
either of two checks passes, and so on. The code in [`_modulus.py`](../src/ukbankcheck/_modulus.py)
names each exception where it's applied.

**How I know it's right.** Vocalink publishes 34 test cases covering every method and
exception. All 34 run in CI against freshly downloaded tables
([`test_spec_cases.py`](../tests/test_spec_cases.py)).
