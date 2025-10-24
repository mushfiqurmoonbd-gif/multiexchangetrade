import argparse
import pandas as pd
from backtester.core import run_backtest
from indicators.rsi import rsi
from indicators.wavetrend import wavetrend
from signals.engine import align_signals

parser = argparse.ArgumentParser()
parser.add_argument('--data', required=True)
parser.add_argument('--rsi_length', type=int, default=14)
parser.add_argument('--rsi_oversold', type=float, default=30.0)
parser.add_argument('--wt_channel', type=int, default=10)
parser.add_argument('--wt_avg', type=int, default=21)
parser.add_argument('--initial_cap', type=float, default=1000.0)
parser.add_argument('--risk_per_trade', type=float, default=0.02)
parser.add_argument('--require_webhook', action='store_true')
parser.add_argument('--stop_loss_pct', type=float, default=0.03)
parser.add_argument('--take_profit_pct', type=float, default=0.06)
parser.add_argument('--max_bars_in_trade', type=int, default=100)
args = parser.parse_args()

df = pd.read_csv(args.data, parse_dates=['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)
df['rsi'] = rsi(df['close'], length=int(args.rsi_length))
if set(['high','low','close']).issubset(df.columns):
    df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3.0
    wt_input = df['hlc3']
else:
    wt_input = df['close']
wt = wavetrend(wt_input, channel_length=int(args.wt_channel), average_length=int(args.wt_avg))
df[['wt1','wt2']] = wt
if 'webhook' not in df.columns:
    df['webhook'] = False
df['signal'] = align_signals(
    df,
    rsi_col='rsi',
    wt1_col='wt1',
    wt2_col='wt2',
    webhook_col='webhook',
    rsi_oversold_threshold=float(args.rsi_oversold),
    require_webhook=bool(args.require_webhook),
)
res = run_backtest(
    df,
    entry_col='signal',
    initial_cap=float(args.initial_cap),
    risk_per_trade=float(args.risk_per_trade),
    stop_loss_pct=float(args.stop_loss_pct),
    take_profit_pct=float(args.take_profit_pct),
    max_bars_in_trade=int(args.max_bars_in_trade),
)
print('Metrics:', res['metrics'])
res['df'].to_csv('backtest_out.csv', index=False)
print('Saved backtest_out.csv')