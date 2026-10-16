"""Integer parity business rule."""


def is_even(n: int) -> bool:
    """Return whether an integer is even; reject bool and non-integers."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an integer, excluding bool")
    return n % 2 == 0
