import pandas as pd
from typing import Dict
from strategies.base import Strategy
from strategies.ema_crossover import EMACrossoverStrategy
from strategies.rsi_bbands import RSIBBandsStrategy
from strategies.grid import GridStrategy


class StrategyManager:
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {
            'ema_crossover': EMACrossoverStrategy(),
            'rsi_bbands': RSIBBandsStrategy(),
            'grid': GridStrategy(),
        }

    def select_by_regime(self, df: pd.DataFrame) -> Strategy:
        # Simple regime heuristic: use ATR/vol and slope of SMA to determine trend vs mean reversion
        price = df['close']
        sma = price.rolling(50, min_periods=1).mean()
        slope = (sma - sma.shift(10)).abs()
        vol = price.pct_change().rolling(20, min_periods=1).std()
        if slope.iloc[-1] > vol.iloc[-1] * 0.5:
            return self.strategies['ema_crossover']
        if vol.iloc[-1] < 0.01:
            return self.strategies['grid']
        return self.strategies['rsi_bbands']

    def run(self, df: pd.DataFrame, preferred: str = None, **params) -> pd.Series:
        if preferred and preferred in self.strategies:
            return self.strategies[preferred].generate_signals(df, **params)
        strat = self.select_by_regime(df)
        return strat.generate_signals(df, **params)


