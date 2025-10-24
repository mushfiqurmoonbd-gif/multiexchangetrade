# Helpers placeholder (position sizing, logging helpers, etc.)
def position_size_usd(account_usd, risk_per_trade, price):
    if price <= 0:
        return 0.0
    return (account_usd * risk_per_trade) / price
