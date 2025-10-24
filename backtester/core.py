import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from utils.metrics import compute_metrics

def run_backtest(
    df: pd.DataFrame,
    entry_col: str = 'signal',
    initial_cap: float = 1000.0,
    risk_per_trade: float = 0.01,
    exit_on_wt_cross_down: bool = True,
    stop_loss_pct: float = 0.03,
    take_profit_pct: float = 0.06,
    max_bars_in_trade: int = 100,
    wt1_col: str = 'wt1',
    wt2_col: str = 'wt2',
    fee_rate: float = 0.0004,
):
    cash = initial_cap
    position: Optional[Dict] = None
    equity: List[float] = []
    trades: List[Dict] = []

    for idx, row in df.iterrows():
        price = float(row['close'])

        # Entry
        if position is None and bool(row.get(entry_col, False)):
            position_size_usd = cash * float(risk_per_trade)
            qty = position_size_usd / price if price > 0 else 0.0
            position = {
                'entry_price': price,
                'qty': qty,
                'entry_idx': idx,
            }
            trades.append({'entry_idx': idx, 'entry_price': price, 'qty': qty})

        # Equity mark-to-market
        if position is not None:
            unreal_pnl = (price - position['entry_price']) * position['qty']
            equity_val = cash + unreal_pnl
        else:
            equity_val = cash
        equity.append(equity_val)

        # Exit rules
        if position is not None:
            entry_price = position['entry_price']
            stop_price = entry_price * (1 - float(stop_loss_pct)) if stop_loss_pct is not None else None
            tp_price = entry_price * (1 + float(take_profit_pct)) if take_profit_pct is not None else None

            should_exit = False

            # SL/TP
            if stop_price is not None and price <= stop_price:
                should_exit = True
            if tp_price is not None and price >= tp_price:
                should_exit = True

            # Cross-down exit
            if not should_exit and exit_on_wt_cross_down and idx > 0 and wt1_col in df.columns and wt2_col in df.columns:
                prev_ge = df[wt1_col].iat[idx-1] >= df[wt2_col].iat[idx-1]
                curr_lt = df[wt1_col].iat[idx] < df[wt2_col].iat[idx]
                if prev_ge and curr_lt:
                    should_exit = True

            # Max bars in trade
            if not should_exit and max_bars_in_trade is not None:
                if (idx - position['entry_idx']) >= int(max_bars_in_trade):
                    should_exit = True

            if should_exit:
                fee = abs(price * position['qty']) * float(fee_rate)
                cash = equity_val - fee
                trades[-1].update({'exit_idx': idx, 'exit_price': price, 'fee': float(fee)})
                position = None

    df = df.copy()
    df['equity'] = equity
    metrics = compute_metrics(df['equity'], trades)
    return {'df': df, 'trades': trades, 'metrics': metrics}
