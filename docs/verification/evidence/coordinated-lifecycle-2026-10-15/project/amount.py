"""Exact formatting of nonnegative integer cents, without external dependencies."""


def format_amount(cents: int) -> str:
    """Return cents as a fixed two-decimal yuan string.

    Reject booleans and other non-integers with TypeError, negatives with
    ValueError. Use bounded decimal chunks to support huge integers without
    changing the interpreter's global integer-to-string safety limit.
    """
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise TypeError("cents must be an integer")
    if cents < 0:
        raise ValueError("cents must be nonnegative")

    yuan, remainder = divmod(cents, 100)
    chunks = []
    while yuan >= 1_000_000_000:
        yuan, chunk = divmod(yuan, 1_000_000_000)
        chunks.append(f"{chunk:09d}")
    whole = str(yuan) + "".join(reversed(chunks))
    return f"{whole}.{remainder:02d}"
