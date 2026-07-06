"""
Derive accurate product prices from dataset CSV rows and price history.
"""


def _safe_float(value, default=0.0):
    try:
        val = float(value)
        if val != val:  # NaN
            return default
        return val
    except (TypeError, ValueError):
        return default


def history_prices_from_row(row, fallback=0.0):
    """Read price_day_1 .. price_day_10 from a CSV row."""
    prices = []
    for day in range(1, 11):
        prices.append(_safe_float(row.get(f"price_day_{day}"), fallback))
    return prices


def compute_prices_from_row(row):
    """
    Return (current_price, old_price, history_prices) from a dataset row.

    - current_price: from CSV current_price (or last day if missing)
    - old_price: highest historical price only if above current (real discount)
    - history_prices: list of 10 daily prices for PriceHistory
    """
    history = history_prices_from_row(row, fallback=0.0)
    current_price = _safe_float(row.get("current_price"), 0.0)

    if current_price <= 0 and history:
        current_price = history[-1]

    if current_price <= 0:
        current_price = max(history) if history else 0.0

    peak = max(history) if history else current_price

    if peak > current_price:
        old_price = peak
    else:
        old_price = current_price

    return current_price, old_price, history


def compute_old_price_from_history(current_price, history_prices):
    """Recompute old_price from existing history list and current price."""
    current_price = _safe_float(current_price, 0.0)
    if not history_prices:
        return current_price

    peak = max(_safe_float(p) for p in history_prices)
    return peak if peak > current_price else current_price
