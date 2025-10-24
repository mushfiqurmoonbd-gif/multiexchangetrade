def position_size_from_risk(cash_usd: float, risk_fraction: float, entry_price: float) -> float:
    if entry_price <= 0:
        return 0.0
    return max(0.0, float(cash_usd) * float(risk_fraction) / float(entry_price))


def apply_sl_tp(entry_price: float, price: float, stop_loss_pct: float, take_profit_pct: float) -> bool:
    if entry_price <= 0:
        return False
    sl = entry_price * (1 - float(stop_loss_pct)) if stop_loss_pct is not None else None
    tp = entry_price * (1 + float(take_profit_pct)) if take_profit_pct is not None else None
    if sl is not None and price <= sl:
        return True
    if tp is not None and price >= tp:
        return True
    return False


