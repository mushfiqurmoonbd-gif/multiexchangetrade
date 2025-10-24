import numpy as np
from typing import List, Dict, Optional

def _compute_equity_metrics(arr: np.ndarray) -> Dict[str, float]:
    if len(arr) < 2:
        return {'sharpe': 0.0, 'max_drawdown': 0.0}
    returns = np.diff(arr) / arr[:-1]
    sharpe = (returns.mean() / (returns.std() + 1e-10)) * (252 ** 0.5)
    peak = np.maximum.accumulate(arr)
    drawdown = (arr - peak) / peak
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0
    return {'sharpe': float(sharpe), 'max_drawdown': max_dd}

def _compute_trade_metrics(trades: List[Dict]) -> Dict[str, float]:
    closed = [t for t in trades if 'exit_price' in t and t['exit_price'] is not None and 'entry_price' in t and 'qty' in t]
    if not closed:
        return {'win_rate': 0.0, 'profit_factor': 1.0}
    pnls = [(t['exit_price'] - t['entry_price']) * t['qty'] for t in closed]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    win_rate = len(wins) / max(1, len(closed))
    gross_profit = sum(wins)
    gross_loss = -sum(losses)  # positive number
    if gross_loss == 0:
        profit_factor = float('inf') if gross_profit > 0 else 1.0
    else:
        profit_factor = gross_profit / gross_loss
    return {'win_rate': float(win_rate), 'profit_factor': float(profit_factor)}

def compute_metrics(equity_series, trades: Optional[List[Dict]] = None) -> Dict[str, float]:
    arr = np.asarray(equity_series)
    eq = _compute_equity_metrics(arr)
    tr = _compute_trade_metrics(trades or [])
    # Merge, prefer trade-based win_rate and profit_factor when available
    out = {**tr, **eq}
    # Fallbacks if no trades
    if not trades:
        # naive fallbacks
        if len(arr) >= 2:
            returns = np.diff(arr) / arr[:-1]
            out['win_rate'] = float((returns > 0).sum() / max(1, len(returns)))
            out['profit_factor'] = float(arr[-1] / arr[0]) if arr[0] > 0 else float('nan')
        else:
            out['win_rate'] = 0.0
            out['profit_factor'] = 1.0
    return out
