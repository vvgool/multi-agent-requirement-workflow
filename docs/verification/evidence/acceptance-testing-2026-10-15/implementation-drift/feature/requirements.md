# Shipping fee fixture (synthetic evaluation approval only)
AC-1: shipping_fee(subtotal_cents) returns 1000 when 0 <= subtotal_cents < 10000, else 0.
AC-2: a negative integer subtotal raises ValueError. Input is integer cents.
AC-3: checkout_total(subtotal_cents) returns subtotal plus shipping fee, including the exact 10000 boundary.
