import pandas as pd

def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    """Return RSI series using Wilder's smoothing."""
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/length, adjust=False).mean()
    ma_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = ma_up / (ma_down.replace(0, 1e-10))
    rsi = 100 - (100 / (1 + rs))
    return rsi
