import pandas as pd
from strategies.base import Strategy


class EMACrossoverStrategy(Strategy):
    name = "ema_crossover"

    def generate_signals(
        self,
        df: pd.DataFrame,
        fast: int = 20,
        slow: int = 50,
        price_col: str = 'close',
        return_mode: str = 'long_only',  # 'long_only' | 'long_short'
        **params
    ) -> pd.DataFrame:
        s = df.copy()
        s['ema_fast'] = s[price_col].ewm(span=int(fast), adjust=False).mean()
        s['ema_slow'] = s[price_col].ewm(span=int(slow), adjust=False).mean()
        cross_up = (s['ema_fast'].shift(1) <= s['ema_slow'].shift(1)) & (s['ema_fast'] > s['ema_slow'])
        cross_down = (s['ema_fast'].shift(1) >= s['ema_slow'].shift(1)) & (s['ema_fast'] < s['ema_slow'])

        if return_mode == 'long_short':
            s['long'] = cross_up.fillna(False)
            s['short'] = cross_down.fillna(False)
            return s[['long', 'short']]
        else:
            s['signal'] = cross_up.fillna(False)
            return s[['signal']]


