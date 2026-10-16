def shipping_fee(subtotal_cents):
    if subtotal_cents < 0:
        raise ValueError("negative subtotal")
    return 1000 if subtotal_cents < 10000 else 0
