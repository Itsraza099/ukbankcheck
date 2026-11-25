"""Property-based tests: Hypothesis generates hundreds of inputs and checks rules
that must hold for *all* of them, rather than one hand-picked example."""

from hypothesis import given
from hypothesis import strategies as st

from ukbankcheck import InvalidFormatError, normalise

digits = st.text(alphabet="0123456789", min_size=6, max_size=6)
accounts = st.text(alphabet="0123456789", min_size=6, max_size=8)
separator_noise = st.text(alphabet=" -", max_size=4)


@given(sort_code=digits, account=accounts)
def test_normalise_is_idempotent(sort_code: str, account: str) -> None:
    once = normalise(sort_code, account)
    assert normalise(once.sort_code, once.account_number) == once


@given(sort_code=digits, account=accounts, noise=separator_noise)
def test_separators_never_change_the_result(sort_code: str, account: str, noise: str) -> None:
    noisy = noise.join(sort_code)
    assert normalise(noisy, account) == normalise(sort_code, account)


@given(sort_code=digits, account=accounts)
def test_padding_preserves_the_number(sort_code: str, account: str) -> None:
    result = normalise(sort_code, account)
    assert len(result.account_number) == 8
    assert int(result.account_number) == int(account)


@given(sort_code=digits, junk=st.text(min_size=1).filter(lambda s: not s.strip(" -").isdigit()))
def test_non_digit_accounts_are_always_rejected(sort_code: str, junk: str) -> None:
    try:
        normalise(sort_code, junk)
    except InvalidFormatError:
        return
    raise AssertionError(f"accepted {junk!r}")
