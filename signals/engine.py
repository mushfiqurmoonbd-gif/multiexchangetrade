import pandas as pd

# alignment policy: all three sources must agree within ±1 candle index
def align_signals(
    df: pd.DataFrame,
    rsi_col: str = 'rsi',
    wt1_col: str = 'wt1',
    wt2_col: str = 'wt2',
    webhook_col: str = 'webhook',
    rsi_oversold_threshold: float = 30.0,
    require_webhook: bool = True,
    enable_rsi_gate: bool = True,
    alignment_window: int = 1,
) -> pd.Series:
    n = len(df)
    out = [False] * n

    def rsi_buy_at(idx):
        return float(df[rsi_col].iat[idx]) < float(rsi_oversold_threshold)

    def wt_cross_up(idx):
        if idx == 0:
            return False
        return (
            df[wt1_col].iat[idx-1] <= df[wt2_col].iat[idx-1]
            and df[wt1_col].iat[idx] > df[wt2_col].iat[idx]
        )

    for i in range(n):
        # allow configurable ±window bars alignment
        for j in range(i - int(alignment_window), i + int(alignment_window) + 1):
            if j < 0 or j >= n:
                continue
            if require_webhook:
                webhook_series = df.get(webhook_col, pd.Series([False] * n, index=df.index))
                webhook_ok = bool(webhook_series.iat[j])
            else:
                webhook_ok = True
            rsi_ok = rsi_buy_at(j) if enable_rsi_gate else True
            if rsi_ok and wt_cross_up(j) and webhook_ok:
                out[i] = True
                break
    return pd.Series(out, index=df.index)

def wt_cross_down(df: pd.DataFrame, wt1_col: str = 'wt1', wt2_col: str = 'wt2') -> pd.Series:
    """Return boolean Series where wt1 crosses below wt2 at bar i."""
    wt1 = df[wt1_col]
    wt2 = df[wt2_col]
    prev_le = wt1.shift(1) >= wt2.shift(1)
    curr_lt = wt1 < wt2
    return (prev_le & curr_lt).fillna(False)
