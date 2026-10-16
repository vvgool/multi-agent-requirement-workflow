from shipping import shipping_fee

def checkout_total(subtotal_cents):
    return subtotal_cents + shipping_fee(subtotal_cents)
