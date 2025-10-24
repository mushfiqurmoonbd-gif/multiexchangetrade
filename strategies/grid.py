import pandas as pd
from strategies.base import Strategy


class GridStrategy(Strategy):
    name = "grid"

    def generate_signals(self, df: pd.DataFrame, grids: int = 8, price_col: str = 'close', **params) -> pd.Series:
        # Simplified: buy when price crosses below the nearest lower grid level from mid
        s = df.copy()
        p = s[price_col]
        pmin, pmax = p.rolling(200, min_periods=1).min(), p.rolling(200, min_periods=1).max()
        mid = (pmin + pmax) / 2.0
        # create grid spacing around mid
        rng = (pmax - pmin).replace(0, 1e-9)
        step = rng / max(1, int(grids))
        lower_grid = mid - step
        signal = (p.shift(1) >= lower_grid.shift(1)) & (p < lower_grid)
        return signal.fillna(False)


