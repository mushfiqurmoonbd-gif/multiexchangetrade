import pandas as pd
from strategies.base import Strategy


class RSIBBandsStrategy(Strategy):
    name = "rsi_bbands"

    def generate_signals(self, df: pd.DataFrame, rsi_len: int = 14, bb_len: int = 20, bb_mult: float = 2.0, price_col: str = 'close', **params) -> pd.Series:
        s = df.copy()
        delta = s[price_col].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/float(rsi_len), adjust=False).mean()
        ma_down = down.ewm(alpha=1/float(rsi_len), adjust=False).mean()
        rs = ma_up / (ma_down.replace(0, 1e-10))
        s['rsi'] = 100 - (100 / (1 + rs))
        s['bb_mid'] = s[price_col].rolling(int(bb_len), min_periods=1).mean()
        std = s[price_col].rolling(int(bb_len), min_periods=1).std().fillna(0)
        s['bb_low'] = s['bb_mid'] - float(bb_mult) * std
        # buy when price below lower band and RSI oversold
        signal = (s[price_col] < s['bb_low']) & (s['rsi'] < 30)
        return signal.fillna(False)


