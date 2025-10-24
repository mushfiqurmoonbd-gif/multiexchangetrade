import pandas as pd

def wavetrend(hlc3: pd.Series, channel_length: int = 10, average_length: int = 21) -> pd.DataFrame:
    """Simplified WaveTrend implementation returning wt1 and wt2."""
    esa = hlc3.ewm(span=channel_length, adjust=False).mean()
    de = (hlc3 - esa).abs().ewm(span=channel_length, adjust=False).mean()
    ci = (hlc3 - esa) / (0.015 * de.replace(0, 1e-10))
    wt1 = ci.ewm(span=average_length, adjust=False).mean()
    wt2 = wt1.ewm(span=4, adjust=False).mean()
    return pd.DataFrame({"wt1": wt1, "wt2": wt2})
