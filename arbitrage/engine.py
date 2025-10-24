import time
from typing import Dict, List
import ccxt


class ArbitrageEngine:
    def __init__(self, exchanges: Dict[str, ccxt.Exchange], symbols: List[str], threshold_bps: float = 10.0):
        self.exchanges = exchanges
        self.symbols = symbols
        self.threshold = float(threshold_bps) / 10000.0
        self.running = False

    def fetch_prices(self) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for name, ex in self.exchanges.items():
            ex.enableRateLimit = True
            ex.timeout = max(getattr(ex, 'timeout', 10000), 15000)
            out[name] = {}
            for sym in self.symbols:
                try:
                    t = ex.fetch_ticker(sym)
                    out[name][sym] = float(t.get('last') or t.get('close') or 0.0)
                except Exception:
                    out[name][sym] = 0.0
        return out

    def find_opportunities(self, prices: Dict[str, Dict[str, float]]):
        opps = []
        if not prices:
            return opps
        names = list(prices.keys())
        for sym in self.symbols:
            vals = [(n, prices[n].get(sym, 0.0)) for n in names]
            vals = [v for v in vals if v[1] > 0]
            if len(vals) < 2:
                continue
            vals.sort(key=lambda x: x[1])
            low, high = vals[0], vals[-1]
            spread = (high[1] - low[1]) / low[1]
            if spread >= self.threshold:
                opps.append({'symbol': sym, 'buy_on': low[0], 'sell_on': high[0], 'spread': spread})
        return opps

    def run_once(self):
        prices = self.fetch_prices()
        return self.find_opportunities(prices)


