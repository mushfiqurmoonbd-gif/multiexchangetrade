import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import time
import os
from datetime import datetime
from indicators.rsi import rsi

def display_account_balance(paper_mode: bool, real_account_data: dict = None):
    """
    Consolidated function to display account balance information
    Always shows balance - paper or real based on mode
    """
    if not paper_mode and real_account_data and real_account_data.get('balance'):
        # Real account data
        real_balance = real_account_data['balance']
        usdt_balance = real_balance.get('USDT', {})
        real_cash = usdt_balance.get('free', 0)
        real_total = usdt_balance.get('total', 0)
        real_used = usdt_balance.get('used', 0)
        
        return f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <div style="text-align: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; 
                           justify-content: center; gap: 0.5rem;">
                    💰 Real Account Balance
                </h4>
            </div>
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; font-weight: 700; color: var(--accent-green);">
                    ${real_cash:,.2f}
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">Total Balance</div>
            </div>
            <div style="display: grid; gap: 0.5rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Available:</span>
                    <span style="color: var(--accent-green); font-weight: 600;">${real_cash:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">In Orders:</span>
                    <span style="color: var(--accent-blue); font-weight: 600;">${real_used:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Total:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">${real_total:,.2f}</span>
                </div>
            </div>
        </div>
        """
    elif not paper_mode:
        # Real trading mode but no account data yet
        return f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <div style="text-align: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; 
                           justify-content: center; gap: 0.5rem;">
                    💰 Real Account Balance
                </h4>
            </div>
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-secondary);">
                    Loading...
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">Connecting to exchange</div>
            </div>
            <div style="text-align: center;">
                <div style="color: var(--text-secondary); font-size: 0.8rem;">
                    Balance will appear automatically when connected
                </div>
            </div>
        </div>
        """
    else:
        # Paper trading mode
        account = st.session_state.get('account', {'cash': 10000, 'equity': [10000]})
        paper_cash = account.get('cash', 10000)
        paper_equity = account.get('equity', [10000])[-1] if account.get('equity') else 10000
        
        return f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <div style="text-align: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; 
                           justify-content: center; gap: 0.5rem;">
                    📊 Paper Account Balance
                </h4>
            </div>
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; font-weight: 700; color: var(--accent-blue);">
                    ${paper_equity:,.2f}
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">Paper Trading Balance</div>
            </div>
            <div style="display: grid; gap: 0.5rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Available Cash:</span>
                    <span style="color: var(--accent-blue); font-weight: 600;">${paper_cash:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Total Equity:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">${paper_equity:,.2f}</span>
                </div>
            </div>
        </div>
        """
from indicators.wavetrend import wavetrend
from signals.engine import align_signals
from backtester.core import run_backtest
from utils.logger import log_trade, log_pnl
from utils.error_handler import error_handler, safe_execute, TradingError, APIError
from executor.ccxt_executor import CCXTExecutor
from strategies.manager import StrategyManager
from utils.risk import position_size_from_risk
from arbitrage.engine import ArbitrageEngine
from utils.configurable_risk import ConfigurableRiskManager, StopLossType
from backtester.comprehensive_metrics import ComprehensiveMetricsCalculator
from backtester.multi_timeframe_analyzer import MultiTimeframeAnalyzer

st.set_page_config(
    page_title="Multi-Exchange Trading Platform", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# Enhanced CSS styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables */
    :root {
        --primary-bg: #0a0e1a;
        --secondary-bg: #1a1f2e;
        --card-bg: #252b3d;
        --border-color: #2d3748;
        --text-primary: #ffffff;
        --text-secondary: #a0aec0;
        --accent-green: #48bb78;
        --accent-red: #f56565;
        --accent-blue: #4299e1;
        --accent-purple: #9f7aea;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --border-radius: 12px;
        --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global Styles */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: var(--primary-bg);
        border-right: 1px solid var(--border-color);
    }
    
    /* Custom Sidebar Header */
    .sidebar-header {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        padding: 1.5rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 var(--border-radius) var(--border-radius);
        text-align: center;
    }
    
    .sidebar-header h1 {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .sidebar-header .subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    /* Section Headers */
    .section-header {
        background: var(--card-bg);
        padding: 0.75rem 1rem;
        margin: 1rem -1rem 1rem -1rem;
        border-left: 4px solid var(--accent-blue);
        border-radius: 0 var(--border-radius) var(--border-radius) 0;
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.95rem;
    }
    
    /* Control Groups */
    .control-group {
        background: var(--secondary-bg);
        padding: 1rem;
        border-radius: var(--border-radius);
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }
    
    /* Status Indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-trading {
        background: rgba(72, 187, 120, 0.1);
        color: var(--accent-green);
        border: 1px solid var(--accent-green);
    }
    
    .status-stopped {
        background: rgba(245, 101, 101, 0.1);
        color: var(--accent-red);
        border: 1px solid var(--accent-red);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
    }
    
    /* Action Buttons */
    .action-button {
        width: 100%;
        padding: 0.75rem;
        border-radius: var(--border-radius);
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, var(--accent-green), #38a169);
        color: white;
    }
    
    .btn-primary:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    .btn-danger {
        background: linear-gradient(135deg, var(--accent-red), #e53e3e);
        color: white;
    }
    
    .btn-danger:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    /* Metric Cards */
    .metric-card {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Strategy Tab Styles */
    .strategy-card {
        background: var(--secondary-bg);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }
    
    .strategy-header {
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .conditions-list {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid var(--accent-blue);
    }
    
    .conditions-list h4 {
        color: var(--accent-blue);
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .conditions-list ul {
        margin: 0;
        padding-left: 1.2rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .conditions-list li {
        margin-bottom: 0.25rem;
    }
    
    .status-box {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid var(--border-color);
    }
    
    .status-text {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .status-details {
        font-size: 0.85rem;
        color: var(--text-secondary);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    # Header Section
    st.markdown("""
    <div class="sidebar-header">
        <h1>🚀 Trading Platform</h1>
        <div class="subtitle">Multi-Exchange Trading Dashboard</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Trading Status
    if 'is_trading' not in st.session_state:
        st.session_state['is_trading'] = False
    
    status_class = "status-trading" if st.session_state['is_trading'] else "status-stopped"
    if st.session_state['is_trading']:
        # Get paper mode from session state or default to True
        paper_mode = st.session_state.get('paper_mode', True)
        status_text = "📝 PAPER TRADING" if paper_mode else "🚀 LIVE TRADING"
    else:
        status_text = "STOPPED"
    status_dot = "status-dot"
    
    st.markdown(f"""
    <div class="status-indicator {status_class}">
        <div class="{status_dot}"></div>
        {status_text}
    </div>
    """, unsafe_allow_html=True)
    
    # Exchange Configuration
    st.markdown('<div class="section-header">🔗 Exchange Setup</div>', unsafe_allow_html=True)
    
    with st.container():
        ex_name = st.selectbox(
            "Select Exchange", 
            ["binance", "bybit", "mexc", "alpaca", "coinbase", "kraken"], 
            index=0,
            help="Choose your preferred exchange (crypto or stocks)"
        )
        
        # Backtest Controls
        st.markdown('<div class="section-header">🧪 Backtest</div>', unsafe_allow_html=True)
        run_bt = st.button("▶️ Run Backtest", key="run_backtest_btn")
        st.session_state.setdefault('backtest_trigger', False)
        if run_bt:
            st.session_state['backtest_trigger'] = True

        # Signal Test
        st.markdown('<div class="section-header">🔎 Signal Test</div>', unsafe_allow_html=True)
        test_sig = st.button("🧪 Test Signals (Buy/Sell)", key="test_signals_btn")
        st.session_state.setdefault('signal_test_trigger', False)
        if test_sig:
            st.session_state['signal_test_trigger'] = True
        
        # Trading Mode Selection
        trading_mode = st.radio(
            "🎯 Trading Mode",
            ["📝 Paper Trading (Practice)", "🚀 Real Trading (Live)"],
            index=0,
            help="Choose between paper trading for practice or real trading with live orders"
        )
        
        paper = "Paper" in trading_mode
        st.session_state['paper_mode'] = paper
        
        # Mode-specific warnings
        if paper:
            st.markdown("""
            <div style="background: var(--accent-blue); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                📝 PAPER TRADING MODE - Safe Practice Environment
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--accent-green); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                🚀 REAL TRADING MODE - Live Trading Enabled
            </div>
            """, unsafe_allow_html=True)
        
        dark_theme = st.checkbox(
            "🌙 Dark Theme", 
            value=True,
            help="Toggle between light and dark themes"
        )
    
    # Market Configuration
    st.markdown('<div class="section-header">📊 Market Settings</div>', unsafe_allow_html=True)
    
    with st.container():
        # Load API from .env when live trading
        ex_upper = ex_name.upper()
        api_key = os.getenv(f"{ex_upper}_API_KEY") if not paper else None
        api_secret = os.getenv(f"{ex_upper}_API_SECRET") if not paper else None
        
        # Special handling for Coinbase (requires passphrase)
        if ex_name.lower() == 'coinbase' and not paper:
            passphrase = os.getenv(f"{ex_upper}_PASSPHRASE")
            if api_key and api_secret and passphrase:
                # For Coinbase, we need to pass the passphrase as well
                _exec = CCXTExecutor(ex_name, api_key, api_secret, paper=paper)
                # Set the passphrase in the exchange options
                if hasattr(_exec.ex, 'options'):
                    _exec.ex.options['passphrase'] = passphrase
            else:
                _exec = CCXTExecutor(ex_name, api_key, api_secret, paper=paper)
        else:
            _exec = CCXTExecutor(ex_name, api_key, api_secret, paper=paper)
        
        # Set appropriate quote currency based on exchange
        if ex_name.lower() in ['alpaca']:
            # US stock exchanges use USD
            quote_currency = "USD"
            popular_pairs = [
                "BTCUSD", "ETHUSD", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
                "NVDA", "META", "NFLX", "AMD", "INTC", "CRM", "ADBE", "PYPL"
            ]
        elif ex_name.lower() in ['coinbase', 'kraken']:
            # US crypto exchanges use USD
            quote_currency = "USD"
            popular_pairs = [
                "BTC-USD", "ETH-USD", "LTC-USD", "BCH-USD", "ETC-USD",
                "XRP-USD", "ADA-USD", "DOT-USD", "LINK-USD", "UNI-USD"
            ]
        else:
            # International crypto exchanges use USDT
            quote_currency = "USDT"
            popular_pairs = [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", 
                "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT",
                "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "FTMUSDT"
            ]
        
        symbols = _exec.list_symbols(quote_currency)
        timeframes = _exec.list_timeframes()
        
        # Filter available symbols and prioritize popular pairs
        if symbols:
            # Convert symbols to uppercase for comparison
            symbols_upper = [s.upper() for s in symbols]
            available_popular = [pair for pair in popular_pairs if pair in symbols_upper]
            other_symbols = [s for s in symbols if s.upper() not in popular_pairs]
            ordered_symbols = available_popular + other_symbols
        else:
            ordered_symbols = popular_pairs
        
        # Find index of default symbol based on exchange
        default_index = 0
        if ex_name.lower() in ['alpaca']:
            # Default to BTCUSD for US stock exchanges
            if "BTCUSD" in ordered_symbols:
                default_index = ordered_symbols.index("BTCUSD")
            elif "BTC/USD" in ordered_symbols:
                default_index = ordered_symbols.index("BTC/USD")
        elif ex_name.lower() in ['coinbase', 'kraken']:
            # Default to BTC-USD for US crypto exchanges
            if "BTC-USD" in ordered_symbols:
                default_index = ordered_symbols.index("BTC-USD")
            elif "BTC/USD" in ordered_symbols:
                default_index = ordered_symbols.index("BTC/USD")
        else:
            # Default to BTCUSDT for international crypto exchanges
            if "BTCUSDT" in ordered_symbols:
                default_index = ordered_symbols.index("BTCUSDT")
            elif "BTC/USDT" in ordered_symbols:
                default_index = ordered_symbols.index("BTC/USDT")
        
        symbol = st.selectbox(
            "Trading Pair", 
            options=ordered_symbols, 
            index=default_index,
            help="Select the cryptocurrency pair to trade (popular pairs shown first)"
        )
        
        timeframe = st.selectbox(
            "Timeframe", 
            options=timeframes, 
            index=timeframes.index("1h") if "1h" in timeframes else 0,
            help="Choose the chart timeframe for analysis"
        )
        
        refresh_secs = st.slider(
            "🔄 Refresh Rate (seconds)", 
            min_value=5, 
            max_value=300, 
            value=30, 
            step=5,
            help="How often to refresh market data"
        )
        
        # Automatic periodic refresh using session timestamp
        # Rerun the app when the chosen refresh interval has elapsed
        now_ts = time.time()
        last_ts = st.session_state.get('last_auto_refresh_ts', 0.0)
        last_interval = st.session_state.get('last_auto_refresh_interval', refresh_secs)
        # If the interval changed, force a new schedule
        if last_interval != refresh_secs:
            st.session_state['last_auto_refresh_interval'] = refresh_secs
            st.session_state['last_auto_refresh_ts'] = now_ts
        elif now_ts - last_ts >= float(refresh_secs):
            st.session_state['last_auto_refresh_ts'] = now_ts
            st.rerun()
    
    # Strategy Configuration
    st.markdown('<div class="section-header">🎯 Strategy Configuration</div>', unsafe_allow_html=True)
    
    with st.container():
        strat_choice = st.selectbox(
            "Strategy Type", 
            ["auto", "ema_crossover", "rsi_bbands", "grid"], 
            index=0,
            help="Select your trading strategy"
        )
        position_mode = st.radio(
            "Position Mode",
            options=["Long only", "Long + Short"],
            index=0,
            horizontal=True,
            help="Choose whether to allow short (sell) entries"
        )
        
        # Strategy-specific parameters
        if strat_choice in ["auto", "rsi_bbands"]:
            rsi_length = st.number_input(
                "RSI Length", 
                min_value=5, 
                max_value=50, 
                value=14,
                help="Period for RSI calculation"
            )
            rsi_oversold = st.number_input(
                "RSI Oversold Level", 
                min_value=10, 
                max_value=50, 
                value=30,
                help="RSI level considered oversold"
            )
        else:
            # Set default values for other strategies
            rsi_length = 14
            rsi_oversold = 30
        
        if strat_choice in ["auto"]:
            wt_channel = st.number_input(
                "WaveTrend Channel", 
                min_value=5, 
                max_value=50, 
                value=10,
                help="Channel length for WaveTrend indicator"
            )
            wt_avg = st.number_input(
                "WaveTrend Average", 
                min_value=5, 
                max_value=50, 
                value=21,
                help="Average length for WaveTrend indicator"
            )
        else:
            # Set default values for other strategies
            wt_channel = 10
            wt_avg = 21
    
    # Multi-Timeframe Analysis Configuration
    st.markdown('<div class="section-header">📊 Multi-Timeframe Analysis</div>', unsafe_allow_html=True)
    
    with st.expander("🔄 Multi-Timeframe Settings", expanded=False):
        enable_mtf = st.checkbox(
            "Enable Multi-Timeframe Analysis",
            value=False,
            help="Analyze multiple timeframes for stronger signals"
        )
        
        if enable_mtf:
            primary_tf = st.selectbox(
                "Primary Timeframe",
                ["15m", "30m", "1H", "4H", "1D"],
                index=2,
                help="Primary timeframe for analysis"
            )
            
            secondary_tfs = st.multiselect(
                "Secondary Timeframes",
                ["15m", "30m", "1H", "4H", "1D", "1W"],
                default=["15m", "4H", "1D"],
                help="Additional timeframes to analyze"
            )
            
            mtf_min_confidence = st.slider(
                "Minimum Confidence",
                min_value=0.3,
                max_value=1.0,
                value=0.6,
                step=0.1,
                help="Minimum confidence threshold for signals"
            )
            
            mtf_min_strength = st.selectbox(
                "Minimum Strength",
                ["weak", "moderate", "strong"],
                index=1,
                help="Minimum signal strength required"
            )
            
            # Timeframe weights
            st.markdown("**Timeframe Weights**")
            tf_weights = {}
            for tf in secondary_tfs:
                tf_weights[tf] = st.slider(
                    f"Weight for {tf}",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.5 if tf in ["1H", "4H"] else 0.3,
                    step=0.1,
                    help=f"Weight for {tf} timeframe"
                )
        else:
            primary_tf = "1H"
            secondary_tfs = []
            mtf_min_confidence = 0.6
            mtf_min_strength = "moderate"
            tf_weights = {}
    
    # Risk Management
    st.markdown('<div class="section-header">⚠️ Risk Management</div>', unsafe_allow_html=True)
    
    with st.container():
        initial_cap = st.number_input(
            "💰 Initial Capital ($)", 
            min_value=100.0, 
            max_value=1000000.0, 
            value=10000.0,
            help="Starting capital for trading"
        )
        
        if 'initial_capital' not in st.session_state:
            st.session_state['initial_capital'] = initial_cap
        
        risk_per_trade = st.slider(
            "Risk per Trade (%)", 
            min_value=0.005, 
            max_value=0.10, 
            value=0.02, 
            step=0.005,
            help="Percentage of capital to risk per trade"
        )
    
    # Advanced Risk Management Configuration
    st.markdown('<div class="section-header">⚙️ Advanced Risk Management</div>', unsafe_allow_html=True)
    
    with st.expander("🔧 Configurable Stop-Loss Settings", expanded=False):
        stop_loss_type = st.selectbox(
            "Stop Loss Type",
            ["percentage", "atr", "support_resistance", "volatility"],
            index=0,
            help="Choose stop loss calculation method"
        )
        
        if stop_loss_type == "percentage":
            stop_loss_value = st.slider(
                "Stop Loss Percentage",
                min_value=0.5,
                max_value=10.0,
                value=2.0,
                step=0.1,
                format="%.1f%%",
                help="Stop loss as percentage of entry price"
            ) / 100
        elif stop_loss_type == "atr":
            stop_loss_value = st.slider(
                "ATR Multiplier",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help="ATR multiplier for stop loss distance"
            )
        elif stop_loss_type == "support_resistance":
            stop_loss_value = st.slider(
                "Support/Resistance Distance",
                min_value=1.0,
                max_value=5.0,
                value=2.0,
                step=0.1,
                format="%.1f%%",
                help="Distance from support/resistance levels"
            ) / 100
        else:  # volatility
            stop_loss_value = st.slider(
                "Volatility Multiplier",
                min_value=1.0,
                max_value=3.0,
                value=2.0,
                step=0.1,
                help="Volatility multiplier for stop loss"
            )
        
        # TP1/TP2/Runner Configuration
        st.markdown("**Take Profit Configuration**")
        tp1_multiplier = st.slider(
            "TP1 Multiplier",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            help="TP1 as multiple of risk"
        )
        
        tp2_multiplier = st.slider(
            "TP2 Multiplier", 
            min_value=2.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="TP2 as multiple of risk"
        )
        
        runner_multiplier = st.slider(
            "Runner Multiplier",
            min_value=3.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            help="Runner activation as multiple of risk"
        )
        
        # Daily Breaker
        daily_breaker_active = st.checkbox(
            "Enable Daily Breaker",
            value=False,
            help="Stop trading after daily loss limit"
        )
        
        if daily_breaker_active:
            daily_loss_limit = st.slider(
                "Daily Loss Limit",
                min_value=1.0,
                max_value=10.0,
                value=5.0,
                step=0.5,
                format="%.1f%%",
                help="Maximum daily loss as percentage of capital"
            ) / 100
        else:
            daily_loss_limit = 0.05
        
        # Additional Risk Parameters
        st.markdown("**Additional Risk Parameters**")
        max_bars_in_trade = st.number_input(
            "Max Bars in Trade", 
            min_value=1, 
            max_value=10000, 
            value=100,
            help="Maximum number of bars to hold a position"
        )
        
        # Legacy parameters for backward compatibility
        stop_loss_pct = stop_loss_value if stop_loss_type == "percentage" else 0.03
        take_profit_pct = tp1_multiplier * stop_loss_pct if stop_loss_type == "percentage" else 0.06
    
    # Initialize session state
    if 'account' not in st.session_state:
        st.session_state['account'] = {'cash': float(initial_cap), 'equity': [float(initial_cap)]}
    if 'position' not in st.session_state:
        st.session_state['position'] = None
    if 'trades' not in st.session_state:
        st.session_state['trades'] = []
    if 'arb_running' not in st.session_state:
        st.session_state['arb_running'] = False
    if 'real_account_data' not in st.session_state:
        st.session_state['real_account_data'] = None
    if 'account_validation' not in st.session_state:
        st.session_state['account_validation'] = None
    
    # Real Account Data Fetching and Validation
    if not paper and api_key and api_secret:
        st.markdown('<div class="section-header">🔐 Account Validation</div>', unsafe_allow_html=True)
        
        # Validate account access
        if st.button("🔍 Validate Account Access", key="validate_account"):
            with st.spinner("Validating account access..."):
                try:
                    validation_result = _exec.validate_account()
                    st.session_state['account_validation'] = validation_result
                    
                    if validation_result['valid']:
                        st.success("✅ Account validation successful!")
                        st.info(f"Balance access: {'✅' if validation_result['balance_available'] else '❌'} | Market data: {'✅' if validation_result['market_data_available'] else '❌'}")
                    else:
                        error_msg = error_handler.get_user_friendly_message(Exception(validation_result['message']))
                        st.error(error_msg)
                        
                        # Show suggestions if available
                        suggestions = error_handler.get_error_suggestions(Exception(validation_result['message']))
                        if suggestions:
                            st.markdown("**💡 Suggestions:**")
                            for suggestion in suggestions:
                                st.markdown(f"• {suggestion}")
                except Exception as e:
                    error_msg = error_handler.get_user_friendly_message(e)
                    st.error(error_msg)
                    
                    # Show suggestions
                    suggestions = error_handler.get_error_suggestions(e)
                    if suggestions:
                        st.markdown("**💡 Suggestions:**")
                        for suggestion in suggestions:
                            st.markdown(f"• {suggestion}")
        
        # Display validation results
        if st.session_state['account_validation']:
            validation = st.session_state['account_validation']
            if validation['valid']:
                st.markdown("""
                <div style="background: var(--accent-green); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                    ✅ ACCOUNT VALIDATED - Ready for Real Trading
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: var(--accent-red); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                    ❌ ACCOUNT VALIDATION FAILED - {validation['message']}
                </div>
                """, unsafe_allow_html=True)
        
        # Fetch real account data
        if st.button("📊 Fetch Real Account Data", key="fetch_account_data"):
            with st.spinner("Fetching real account data..."):
                try:
                    account_data = _exec.get_account_info()
                    st.session_state['real_account_data'] = account_data
                    st.success("✅ Real account data fetched successfully!")
                except Exception as e:
                    error_msg = error_handler.get_user_friendly_message(e)
                    st.error(error_msg)
                    
                    # Show suggestions
                    suggestions = error_handler.get_error_suggestions(e)
                    if suggestions:
                        st.markdown("**💡 Suggestions:**")
                        for suggestion in suggestions:
                            st.markdown(f"• {suggestion}")
        
        # Always show balance - automatic display
        st.markdown(display_account_balance(paper, st.session_state.get('real_account_data')), unsafe_allow_html=True)
        
        # Display real account data
        if st.session_state['real_account_data']:
            real_data = st.session_state['real_account_data']
            
            # Real Positions Display
            if real_data.get('positions'):
                positions = real_data['positions']
                if positions:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0;">
                        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📈 Real Positions ({len(positions)})</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for pos in positions[:5]:  # Show first 5 positions
                        symbol = pos.get('symbol', 'Unknown')
                        size = pos.get('size', 0)
                        side = pos.get('side', 'Unknown')
                        unrealized_pnl = pos.get('unrealizedPnl', 0)
                        pnl_color = "var(--accent-green)" if float(unrealized_pnl) >= 0 else "var(--accent-red)"
                        
                        st.markdown(f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0; border-left: 4px solid {pnl_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--text-primary); font-weight: 600;">{symbol}</span>
                                <span style="color: {pnl_color}; font-weight: 600;">${float(unrealized_pnl):,.2f}</span>
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.9rem;">
                                {side} • Size: {size}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0; text-align: center;">
                        <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">📈 Real Positions</h4>
                        <p style="color: var(--text-secondary); margin: 0;">No open positions</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Real Orders Display
            if real_data.get('orders'):
                orders = real_data['orders']
                if orders:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0;">
                        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📋 Real Orders ({len(orders)})</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for order in orders[:5]:  # Show first 5 orders
                        order_id = order.get('orderId', 'Unknown')
                        symbol = order.get('symbol', 'Unknown')
                        side = order.get('side', 'Unknown')
                        qty = order.get('qty', 0)
                        status = order.get('orderStatus', 'Unknown')
                        
                        st.markdown(f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--text-primary); font-weight: 600;">{symbol}</span>
                                <span style="color: var(--text-secondary); font-size: 0.9rem;">{status}</span>
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.9rem;">
                                {side} • Qty: {qty} • ID: {order_id[:8]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0; text-align: center;">
                        <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">📋 Real Orders</h4>
                        <p style="color: var(--text-secondary); margin: 0;">No open orders</p>
                    </div>
                    """, unsafe_allow_html=True)

    # Trading Controls
    st.markdown('<div class="section-header">🎮 Trading Controls</div>', unsafe_allow_html=True)
    
    # Mode-specific warnings and controls
    if paper:
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 2px solid var(--accent-blue); margin: 1rem 0;">
            <h4 style="color: var(--accent-blue); margin: 0 0 0.5rem 0;">📝 PAPER TRADING MODE</h4>
            <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">
                Safe practice environment - No real money at risk:
                <br>• Simulated orders and positions
                <br>• Real market data for realistic testing
                <br>• Perfect for strategy development
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 2px solid var(--accent-green); margin: 1rem 0;">
            <h4 style="color: var(--accent-green); margin: 0 0 0.5rem 0;">🚀 REAL TRADING MODE</h4>
            <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">
                Live Trading Enabled - Ensure you have:
                <br>• Valid API keys configured
                <br>• Sufficient account balance
                <br>• Proper risk management settings
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        button_text = "▶️ Start Paper Trading" if paper else "▶️ Start REAL Trading"
        
        # Check if real trading is ready
        real_trading_ready = True
        if not paper:
            if not api_key or not api_secret:
                real_trading_ready = False
            elif st.session_state['account_validation'] and not st.session_state['account_validation']['valid']:
                real_trading_ready = False
        
        if st.button(button_text, disabled=st.session_state['is_trading'] or not real_trading_ready, key="start_trading"):
            if paper:
                st.session_state['is_trading'] = True
                st.success("📝 PAPER TRADING STARTED - Safe practice mode!")
            else:
                # Additional safety check for real trading
                if api_key and api_secret:
                    if st.session_state['account_validation'] and st.session_state['account_validation']['valid']:
                        st.session_state['is_trading'] = True
                        st.success("🚀 REAL TRADING STARTED - Live trading enabled!")
                    else:
                        st.error("❌ Account validation required before real trading!")
                else:
                    st.error("❌ API keys required for real trading!")
        
        # Show trading readiness status
        if not paper and not real_trading_ready:
            if not api_key or not api_secret:
                st.error("❌ API keys required for real trading!")
            elif st.session_state['account_validation'] and not st.session_state['account_validation']['valid']:
                st.error("❌ Account validation failed - fix issues before trading!")
            else:
                st.warning("⚠️ Validate account access before starting real trading!")
    
    with col_b:
        stop_text = "⏹️ Stop Trading" if paper else "⏹️ EMERGENCY STOP"
        if st.button(stop_text, disabled=not st.session_state['is_trading'], key="stop_trading"):
            st.session_state['is_trading'] = False
            if paper:
                st.warning("📝 Paper trading stopped!")
            else:
                st.warning("🛑 REAL TRADING STOPPED - All positions closed!")
    
    # Arbitrage Scanner
    st.markdown('<div class="section-header">🔍 Arbitrage Scanner</div>', unsafe_allow_html=True)
    
    arb_enabled = st.toggle(
        "Enable Arbitrage Scanner", 
        value=st.session_state['arb_running'],
        help="Scan for arbitrage opportunities across exchanges"
    )
    st.session_state['arb_running'] = arb_enabled
    
    # Trading Mode Indicator
    if not paper and st.session_state['real_account_data'] and st.session_state['real_account_data'].get('balance'):
        mode_indicator = """
        <div style="background: linear-gradient(135deg, #48bb78, #38a169); color: white; padding: 0.75rem; 
                    border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600; font-size: 0.9rem;">
            🚀 REAL TRADING MODE - Live Account Data
        </div>
        """
    else:
        mode_indicator = """
        <div style="background: linear-gradient(135deg, #4299e1, #3182ce); color: white; padding: 0.75rem; 
                    border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600; font-size: 0.9rem;">
            📊 PAPER TRADING MODE - Simulated Data
        </div>
        """
    
    st.markdown(mode_indicator, unsafe_allow_html=True)
    
    # Account Summary removed - Balance now only shows in sidebar
    
    # Position Summary - Only show if there's an active position
    if st.session_state['position'] is not None:
        p = st.session_state['position']
        # Use entry price as fallback since df is not available in sidebar
        pnl = 0.0  # Will be calculated in main section
        pnl_color = "#48bb78" if pnl >= 0 else "#f56565"
        
        st.markdown(f"""
        <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; 
                    border: 1px solid var(--border-color); margin: 1rem 0; text-align: center;">
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Active Position</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {pnl_color};">${pnl:,.2f}</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">Unrealized P&L</div>
        </div>
        """, unsafe_allow_html=True)

# Main Dashboard Header
st.markdown("""
<div style="background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)); 
            padding: 2rem; border-radius: var(--border-radius); margin-bottom: 2rem; 
            text-align: center; color: white;">
    <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
        📊 Live Trading Dashboard
    </h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Real-time market analysis and automated trading
    </p>
</div>
""", unsafe_allow_html=True)

# Data Processing Section
with st.spinner("🔄 Loading market data..."):
    try:
        # Fetch OHLCV
        df = _exec.fetch_ohlcv_df(symbol, timeframe=timeframe, limit=500)
        
        # Validate required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame missing required columns: {required_columns}")
        
        # Check if data is empty
        if len(df) == 0:
            raise ValueError("No data returned from exchange")
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # If user requested signal test, compute and show quick summary
        if st.session_state.get('signal_test_trigger'):
            st.session_state['signal_test_trigger'] = False
            with st.spinner("Testing signals..."):
                try:
                    from indicators.weighted_signals import generate_weighted_signals
                    sig = generate_weighted_signals(df).astype(bool)
                    df['signal'] = sig
                    buy_count = int(sig.sum())
                    sell_count = int((~sig).sum())
                    last_sig = 'BUY' if bool(sig.iloc[-1]) else 'SELL'
                    st.success(f"Signals ready — BUY: {buy_count}, SELL: {sell_count}, Latest: {last_sig}")
                except Exception as e:
                    st.error(f"Signal test failed: {e}")

        # Indicators & signals
        df['rsi'] = rsi(df['close'], length=int(rsi_length))
        
        # Calculate hlc3 if columns exist
        if set(['high', 'low', 'close']).issubset(df.columns):
            df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3.0
            wt_input = df['hlc3']
        else:
            wt_input = df['close']
        
        # Compute wavetrend and ensure correct assignment
        wt = wavetrend(wt_input, channel_length=int(wt_channel), average_length=int(wt_avg))
        if isinstance(wt, pd.DataFrame):
            df[['wt1', 'wt2']] = wt[['wt1', 'wt2']]
        elif isinstance(wt, (list, tuple)) and len(wt) == 2:
            df['wt1'], df['wt2'] = wt
        else:
            raise ValueError("wavetrend function returned unexpected output format")
        
        df['webhook'] = False
        sm = StrategyManager()
        
        # Generate signals based on selected strategy
        if strat_choice == 'auto':
            # Auto strategy: Combine RSI + WaveTrend signals
            # Buy when RSI is oversold AND WaveTrend crosses up
            rsi_oversold_condition = df['rsi'] < rsi_oversold
            wt_cross_up = (df['wt1'].shift(1) <= df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
            df['signal'] = rsi_oversold_condition & wt_cross_up
        elif strat_choice == 'ema_crossover':
            return_mode = 'long_short' if position_mode == 'Long + Short' else 'long_only'
            sig_df = sm.strategies['ema_crossover'].generate_signals(df, return_mode=return_mode)
            if return_mode == 'long_short':
                df[['long', 'short']] = sig_df[['long', 'short']]
            else:
                df[['signal']] = sig_df[['signal']]
        elif strat_choice == 'rsi_bbands':
            df['signal'] = sm.strategies['rsi_bbands'].generate_signals(df, rsi_len=int(rsi_length))
        elif strat_choice == 'grid':
            df['signal'] = sm.strategies['grid'].generate_signals(df)
        else:
            # Fallback to auto strategy
            rsi_oversold_condition = df['rsi'] < rsi_oversold
            wt_cross_up = (df['wt1'].shift(1) <= df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
            df['signal'] = rsi_oversold_condition & wt_cross_up
        
        # Market Overview Section
        last_close = float(df['close'].iat[-1]) if len(df) else 0.0
        prev_close = float(df['close'].iat[-2]) if len(df) > 1 else last_close

        # Calculate 24h change (last 24 bars for hourly data, or adjust based on timeframe)
        if len(df) >= 24:
            price_24h_ago = float(df['close'].iat[-24])
            price_change_24h = last_close - price_24h_ago
            price_change_24h_pct = (price_change_24h / price_24h_ago * 100) if price_24h_ago else 0
        else:
            # Fallback to previous bar if not enough data
            price_change_24h = last_close - prev_close
            price_change_24h_pct = (price_change_24h / prev_close * 100) if prev_close else 0

        # Current bar change
        price_change = last_close - prev_close
        price_change_pct = (price_change / prev_close * 100) if prev_close else 0
        up = price_change_24h >= 0

        st.success("✅ Market data loaded successfully!")

    except Exception as e:
        st.error(f"❌ Data Processing Error: {e}")
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <h3 style="color: var(--accent-red); margin-top: 0;">⚠️ Unable to Load Market Data</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Please check your internet connection and exchange settings. 
                Make sure the selected trading pair is available on the chosen exchange.
            </p>
            <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; 
                        border-left: 4px solid var(--accent-red);">
                <strong>Error Details:</strong><br>
                <code style="color: var(--text-primary);">{}</code>
            </div>
        </div>
        """.format(str(e)), unsafe_allow_html=True)
        st.stop()

# Check if data was loaded successfully
if 'df' not in locals() or df is None or len(df) == 0:
    st.error("❌ No market data available. Please check your exchange settings and try again.")
    st.stop()

# Market Overview Section
last_close = float(df['close'].iat[-1]) if len(df) else 0.0
prev_close = float(df['close'].iat[-2]) if len(df) > 1 else last_close

# Calculate 24h change (last 24 bars for hourly data, or adjust based on timeframe)
if len(df) >= 24:
    price_24h_ago = float(df['close'].iat[-24])
    price_change_24h = last_close - price_24h_ago
    price_change_24h_pct = (price_change_24h / price_24h_ago * 100) if price_24h_ago else 0
else:
    # Fallback to previous bar if not enough data
    price_change_24h = last_close - prev_close
    price_change_24h_pct = (price_change_24h / prev_close * 100) if prev_close else 0

# Current bar change
price_change = last_close - prev_close
price_change_pct = (price_change / prev_close * 100) if prev_close else 0
up = price_change_24h >= 0

# Market Header with Key Metrics
st.markdown(f"""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div>
            <h2 style="margin: 0; color: var(--text-primary); font-size: 1.8rem;">
                📈 {symbol} • {ex_name.upper()}
            </h2>
            <p style="margin: 0.25rem 0 0 0; color: var(--text-secondary); font-size: 0.95rem;">
                {timeframe} • Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')}
            </p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 2rem; font-weight: 700; color: var(--text-primary);">
                ${last_close:,.6f}
            </div>
            <div style="font-size: 1rem; color: {'var(--accent-green)' if up else 'var(--accent-red)'}; 
                        font-weight: 600;">
                24h: {price_change_24h:+.6f} ({price_change_24h_pct:+.2f}%)
            </div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
                1h: {price_change:+.6f} ({price_change_pct:+.2f}%)
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Chart Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📊 Price Chart & Technical Analysis
    </h3>
""", unsafe_allow_html=True)

show_volume = 'volume' in df.columns
rows = 3 if show_volume else 2
fig = make_subplots(
    rows=rows, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.02,
    row_heights=[0.6, 0.25] + ([0.15] if show_volume else []),
    subplot_titles=['Price Action', 'WaveTrend Oscillator'] + (['Volume'] if show_volume else [])
)

# Main candlestick chart
fig.add_trace(
    go.Candlestick(
        x=df['timestamp'], 
        open=df['open'], 
        high=df['high'], 
        low=df['low'], 
        close=df['close'], 
        name='OHLC',
        increasing_line_color='#48bb78',
        decreasing_line_color='#f56565',
        increasing_fillcolor='rgba(72, 187, 120, 0.1)',
        decreasing_fillcolor='rgba(245, 101, 101, 0.1)'
    ),
    row=1, col=1
)

# WaveTrend indicators
fig.add_trace(
    go.Scatter(
        x=df['timestamp'], 
        y=df['wt1'], 
        name='WT1', 
        line=dict(color='#48bb78', width=2),
        hovertemplate='WT1: %{y:.2f}<extra></extra>'
    ), 
    row=2, col=1
)
fig.add_trace(
    go.Scatter(
        x=df['timestamp'], 
        y=df['wt2'], 
        name='WT2', 
        line=dict(color='#a0aec0', width=2),
        hovertemplate='WT2: %{y:.2f}<extra></extra>'
    ), 
    row=2, col=1
)

# Trading signals
try:
    sig_idx = df.index[df['signal'] == True]
    if len(sig_idx) > 0:
        fig.add_trace(
            go.Scatter(
                x=df.loc[sig_idx, 'timestamp'],
                y=df.loc[sig_idx, 'close'],
                mode='markers+text',
                name='Buy Signals',
                marker=dict(
                    symbol='triangle-up', 
                    size=15, 
                    color='#48bb78', 
                    line=dict(width=2, color='#2d7d32')
                ),
                text=['BUY'] * len(sig_idx),
                textposition='top center',
                textfont=dict(color='white', size=10),
                hovertemplate='<b>BUY Signal</b><br>Time: %{x}<br>Price: $%{y:.6f}<extra></extra>'
            ),
            row=1, col=1
        )
except Exception:
    pass

# Volume chart
if show_volume:
    fig.add_trace(
        go.Bar(
            x=df['timestamp'], 
            y=df['volume'], 
            name='Volume', 
            marker_color='#4299e1',
            opacity=0.7,
            hovertemplate='Volume: %{y:,.0f}<extra></extra>'
        ), 
        row=3, col=1
    )

# Chart styling
fig.update_layout(
    template='plotly_dark' if dark_theme else 'plotly_white',
    height=600,
    margin=dict(l=20, r=20, t=40, b=20),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    xaxis_rangeslider_visible=False,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

fig.update_xaxes(showgrid=True, gridcolor='rgba(160, 174, 192, 0.1)')
fig.update_yaxes(showgrid=True, gridcolor='rgba(160, 174, 192, 0.1)')

st.plotly_chart(fig, use_container_width=True, config={
    'displaylogo': False,
    'responsive': True,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'pan2d', 'zoom2d', 'autoScale2d'],
    'displayModeBar': True
})

st.markdown("</div>", unsafe_allow_html=True)

# Technical Indicators Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📊 Technical Indicators
    </h3>
""", unsafe_allow_html=True)

# KPI Cards
k1, k2, k3, k4 = st.columns(4)
with k1:
    rsi_val = float(df['rsi'].iat[-1])
    rsi_color = "#f56565" if rsi_val > 70 else "#48bb78" if rsi_val < 30 else "#a0aec0"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {rsi_color}">{rsi_val:.1f}</div>
        <div class="metric-label">RSI (14)</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    wt1_val = float(df['wt1'].iat[-1])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{wt1_val:.2f}</div>
        <div class="metric-label">WaveTrend 1</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    wt2_val = float(df['wt2'].iat[-1])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{wt2_val:.2f}</div>
        <div class="metric-label">WaveTrend 2</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    chg_color = "#48bb78" if price_change_24h_pct >= 0 else "#f56565"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {chg_color}">{price_change_24h_pct:+.2f}%</div>
        <div class="metric-label">24h Change</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Recent Data Table
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📋 Recent Market Data
    </h3>
""", unsafe_allow_html=True)

# Style the dataframe
styled_df = df.tail(20).copy()
styled_df['timestamp'] = pd.to_datetime(styled_df['timestamp']).dt.strftime('%H:%M:%S')
styled_df = styled_df.round(6)

st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Trading Status Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        💼 Trading Status & Positions
    </h3>
""", unsafe_allow_html=True)

cpos, cords = st.columns([1, 2])
with cpos:
    if st.session_state['position'] is not None:
        p = st.session_state['position']
        pnl = (last_close - p['entry_price']) * p['qty']
        pnl_color = "#48bb78" if pnl >= 0 else "#f56565"
        bars_in_trade = len(df) - p['entry_idx'] if 'entry_idx' in p else 0
        
        st.markdown(f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                📈 Open Position
            </h4>
            <div style="display: grid; gap: 0.75rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Entry Price:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">${p['entry_price']:.6f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Quantity:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">{p['qty']:.6f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Unrealized P&L:</span>
                    <span style="color: {pnl_color}; font-weight: 700;">${pnl:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Bars in Trade:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">{bars_in_trade}</span>
                </div>
                <hr style="border-color: var(--border-color); margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Stop Loss:</span>
                    <span style="color: var(--accent-red); font-weight: 600;">${(p['entry_price']*(1-float(stop_loss_pct))):.6f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Take Profit:</span>
                    <span style="color: var(--accent-green); font-weight: 600;">${(p['entry_price']*(1+float(take_profit_pct))):.6f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                ⏳ No Open Position
            </h4>
            <p style="color: var(--text-secondary); margin: 0;">
                Waiting for next trading signal...
            </p>
        </div>
        """, unsafe_allow_html=True)

with cords:
    if st.session_state['trades']:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                📋 Recent Trades
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        trades_df = pd.DataFrame(st.session_state['trades'])
        if not trades_df.empty:
            trades_df = trades_df.tail(10)  # Show only last 10 trades
            st.markdown(trades_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                📊 No Trades Yet
            </h4>
            <p style="color: var(--text-secondary); margin: 0;">
                Start trading to see your trade history here.
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Indicator Sparklines Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📈 Indicator Trends
    </h3>
""", unsafe_allow_html=True)

spr1, spr2, spr3 = st.columns(3)
with spr1:
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(
        x=df['timestamp'].tail(100), 
        y=df['rsi'].tail(100), 
        mode='lines', 
        line=dict(color="#4299e1", width=2),
        name="RSI"
    ))
    rsi_fig.update_layout(
        height=150, 
        margin=dict(l=10, r=10, t=20, b=10), 
        xaxis_visible=False, 
        yaxis_title="RSI",
        template='plotly_dark' if dark_theme else 'plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    rsi_fig.update_yaxes(range=[0, 100])
    st.plotly_chart(rsi_fig, use_container_width=True, config={'displaylogo': False, 'modeBarButtonsToRemove': ['select2d','lasso2d']})

with spr2:
    wt1_fig = go.Figure()
    wt1_fig.add_trace(go.Scatter(
        x=df['timestamp'].tail(100), 
        y=df['wt1'].tail(100), 
        mode='lines', 
        line=dict(color="#48bb78", width=2),
        name="WT1"
    ))
    wt1_fig.update_layout(
        height=150, 
        margin=dict(l=10, r=10, t=20, b=10), 
        xaxis_visible=False, 
        yaxis_title="WT1",
        template='plotly_dark' if dark_theme else 'plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(wt1_fig, use_container_width=True, config={'displaylogo': False, 'modeBarButtonsToRemove': ['select2d','lasso2d']})

with spr3:
    wt2_fig = go.Figure()
    wt2_fig.add_trace(go.Scatter(
        x=df['timestamp'].tail(100), 
        y=df['wt2'].tail(100), 
        mode='lines', 
        line=dict(color="#a0aec0", width=2),
        name="WT2"
    ))
    wt2_fig.update_layout(
        height=150, 
        margin=dict(l=10, r=10, t=20, b=10), 
        xaxis_visible=False, 
        yaxis_title="WT2",
        template='plotly_dark' if dark_theme else 'plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(wt2_fig, use_container_width=True, config={'displaylogo': False, 'modeBarButtonsToRemove': ['select2d','lasso2d']})

st.markdown("</div>", unsafe_allow_html=True)

latest_idx = len(df) - 1
latest_price = float(df['close'].iat[latest_idx]) if not pd.isna(df['close'].iat[latest_idx]) else 0.0
signal_now = bool(df['signal'].iat[latest_idx])
wt_cross_down_now = False
if latest_idx > 0:  # Prevent index out of bounds
    wt_cross_down_now = (df['wt1'].iat[latest_idx-1] >= df['wt2'].iat[latest_idx-1]) and (df['wt1'].iat[latest_idx] < df['wt2'].iat[latest_idx])

# Show latest signal badge
sig_badge = "No signal"
sig_color = "#8899aa"
if signal_now:
    sig_badge = "BUY signal"
    sig_color = "#22cc88"

    if st.session_state['is_trading']:
        try:
            # Mode-specific trading logic
            paper_mode = st.session_state.get('paper_mode', True)
            if paper_mode:
                print(f"PAPER_TRADING: Processing simulated trades for {symbol}")
            else:
                print(f"REAL_TRADING: Processing trades for {symbol}")
            
            # Exit logic
            if st.session_state['position'] is not None:
                pos = st.session_state['position']
                entry_price = pos['entry_price']
                qty = pos['qty']
                stop_price = entry_price * (1 - float(stop_loss_pct))
                tp_price = entry_price * (1 + float(take_profit_pct))
                bars_in_trade = latest_idx - pos['entry_idx']
                should_exit = False
                if latest_price <= stop_price or latest_price >= tp_price:
                    should_exit = True
                if not should_exit and wt_cross_down_now:
                    should_exit = True
                if not should_exit and bars_in_trade >= int(max_bars_in_trade):
                    should_exit = True
                if should_exit:
                    side = 'sell' if qty > 0 else 'buy'
                    order = _exec.place_market_order(symbol, side, abs(qty))
                    pnl = (latest_price - entry_price) * qty
                    st.session_state['account']['cash'] += pnl
                    if st.session_state['trades']:
                        st.session_state['trades'][-1].update({
                            'exit_idx': latest_idx, 
                            'exit_price': latest_price,
                            'pnl': pnl
                        })
                    try:
                        log_trade('logs/trades.csv', {
                            'symbol': symbol,
                            'side': side,
                            'qty': abs(qty),
                            'price': latest_price,
                            'pnl': pnl,
                            'ts': int(time.time()*1000)
                        })
                    except Exception:
                        pass
                    st.session_state['position'] = None

            # Entry logic - Only trade when strategy generates signal
            if st.session_state['position'] is None and signal_now and not pd.isna(latest_price) and latest_price > 0:
                # Validate signal is from current strategy
                current_rsi = float(df['rsi'].iat[latest_idx])
                current_wt1 = float(df['wt1'].iat[latest_idx])
                current_wt2 = float(df['wt2'].iat[latest_idx])
                
                # Additional validation for auto strategy
                if strat_choice == 'auto':
                    rsi_valid = current_rsi < rsi_oversold
                    wt_valid = current_wt1 > current_wt2
                    if rsi_valid and wt_valid:
                        risk_usd = st.session_state['account']['cash'] * float(risk_per_trade)
                        qty = position_size_from_risk(st.session_state['account']['cash'], float(risk_per_trade), latest_price)
                        if qty > 0:
                            order = _exec.place_market_order(symbol, 'buy', qty)
                            st.session_state['position'] = {
                                'entry_price': latest_price, 
                                'qty': qty, 
                                'entry_idx': latest_idx,
                                'strategy': strat_choice,
                                'entry_rsi': current_rsi,
                                'entry_wt1': current_wt1,
                                'entry_wt2': current_wt2
                            }
                            st.session_state['trades'].append({
                                'entry_idx': latest_idx, 
                                'entry_price': latest_price, 
                                'qty': qty,
                                'strategy': strat_choice,
                                'entry_rsi': current_rsi
                            })
                            try:
                                log_trade('logs/trades.csv', {
                                    'symbol': symbol,
                                    'side': 'buy',
                                    'qty': qty,
                                    'price': latest_price,
                                    'strategy': strat_choice,
                                    'rsi': current_rsi,
                                    'ts': int(time.time()*1000)
                                })
                            except Exception:
                                pass
                else:
                    # For other strategies, use the signal as is
                    risk_usd = st.session_state['account']['cash'] * float(risk_per_trade)
                    qty = position_size_from_risk(st.session_state['account']['cash'], float(risk_per_trade), latest_price)
                    if qty > 0:
                        order = _exec.place_market_order(symbol, 'buy', qty)
                        st.session_state['position'] = {
                            'entry_price': latest_price, 
                            'qty': qty, 
                            'entry_idx': latest_idx,
                            'strategy': strat_choice
                        }
                        st.session_state['trades'].append({
                            'entry_idx': latest_idx, 
                            'entry_price': latest_price, 
                            'qty': qty,
                            'strategy': strat_choice
                        })
                        try:
                            log_trade('logs/trades.csv', {
                                'symbol': symbol,
                                'side': 'buy',
                                'qty': qty,
                                'price': latest_price,
                                'strategy': strat_choice,
                                'ts': int(time.time()*1000)
                            })
                        except Exception:
                            pass

            # Equity tracking
            if st.session_state['position'] is not None:
                pos = st.session_state['position']
                unreal = (latest_price - pos['entry_price']) * pos['qty']
                equity_val = st.session_state['account']['cash'] + unreal
            else:
                equity_val = st.session_state['account']['cash']
            st.session_state['account']['equity'].append(float(equity_val))
            try:
                log_pnl('logs/equity.csv', float(equity_val))
            except Exception:
                pass

        except Exception as e:
            st.error(f"Trading Logic Error: {e}")
            st.session_state['is_trading'] = False  # Stop trading on error

# Right Sidebar - Enhanced Tabs
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📊 Market Analysis & Tools
    </h3>
""", unsafe_allow_html=True)

tabs = st.tabs(["🎯 Strategy", "💼 Account", "📋 Orders", "📈 Market", "🚨 Signals", "🔍 Arbitrage", "⚙️ Order Management", "📊 Comprehensive Metrics", "🚨 Error Log"]) 

with tabs[0]:
    # Get current strategy name
    current_strategy = strat_choice if 'strat_choice' in locals() else 'auto'
    strategy_name = {
        'auto': 'RSI + WaveTrend (Auto)',
        'ema_crossover': 'EMA Crossover',
        'rsi_bbands': 'RSI + Bollinger Bands',
        'grid': 'Grid Trading'
    }.get(current_strategy, 'RSI + WaveTrend (Auto)')
    
    # Calculate values first to avoid f-string format errors
    sl_display = f"{(stop_loss_pct * 100):.1f}%"
    tp_display = f"{(take_profit_pct * 100):.1f}%"
    max_bars_display = max_bars_in_trade
    rsi_threshold = rsi_oversold
    refresh_display = refresh_secs
    is_trading = 'is_trading' in st.session_state and st.session_state['is_trading']
    last_signal = 'BUY' if 'df' in locals() and len(df) > 0 and 'signal' in df.columns and bool(df['signal'].iat[-1]) else 'No Signal'
    
    st.markdown(f"""
    <div class="strategy-card">
        <div class="strategy-header">
            🎯 Active Strategy: {strategy_name}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Entry Conditions
    with st.container():
        st.markdown("""
        <div class="conditions-list">
            <h4>Entry Conditions</h4>
            <ul>
        """, unsafe_allow_html=True)
        
        if current_strategy in ['auto', 'rsi_bbands']:
            st.markdown(f'<li>RSI below oversold threshold ({rsi_threshold})</li>', unsafe_allow_html=True)
        if current_strategy == 'auto':
            st.markdown('<li>WaveTrend cross up (WT1 > WT2)</li>', unsafe_allow_html=True)
        if current_strategy == 'ema_crossover':
            st.markdown('<li>EMA Fast crosses above EMA Slow</li>', unsafe_allow_html=True)
        if current_strategy == 'rsi_bbands':
            st.markdown('<li>Price below Bollinger Lower Band</li>', unsafe_allow_html=True)
        if current_strategy == 'grid':
            st.markdown('<li>Price crosses below grid level</li>', unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    # Exit Conditions
    with st.container():
        st.markdown(f"""
        <div class="conditions-list">
            <h4>Exit Conditions</h4>
            <ul>
                <li>Stop Loss: {sl_display}</li>
                <li>Take Profit: {tp_display}</li>
        """, unsafe_allow_html=True)
        
        if current_strategy == 'auto':
            st.markdown('<li>WaveTrend cross down</li>', unsafe_allow_html=True)
        
        st.markdown(f'<li>Max bars in trade: {max_bars_display}</li></ul></div>', unsafe_allow_html=True)
    
    # Strategy Status
    status_color = "var(--accent-green)" if is_trading else "var(--accent-red)"
    status_emoji = "🟢 LIVE TRADING" if is_trading else "🔴 STOPPED"
    
    st.markdown(f"""
    <div class="status-box">
        <div class="status-text" style="color: {status_color};">{status_emoji}</div>
        <div class="status-details">
            Last signal: {last_signal} • Next refresh: {refresh_display}s
        </div>
    </div>
    """, unsafe_allow_html=True)

with tabs[1]:
    # Account tab - Balance removed, now only shows in sidebar
    st.markdown("""
    <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                border: 1px solid var(--border-color); text-align: center;">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">
            📊 Account Information
        </h4>
        <p style="color: var(--text-secondary); margin: 0;">
            Balance information is now displayed in the sidebar for easy access.
        </p>
    </div>
    """, unsafe_allow_html=True)

with tabs[2]:
    # Show real trading data if available, otherwise show simulated data
    if not paper and st.session_state['real_account_data'] and st.session_state['real_account_data'].get('trades'):
        # Real trading history
        real_trades = st.session_state['real_account_data']['trades']
        if real_trades:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                    📋 Real Trading History
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Display real trades
            for trade in real_trades[:10]:  # Show last 10 real trades
                symbol = trade.get('symbol', 'Unknown')
                side = trade.get('side', 'Unknown')
                qty = trade.get('qty', 0)
                price = trade.get('price', 0)
                timestamp = trade.get('timestamp', 0)
                
                # Format timestamp
                try:
                    if timestamp:
                        trade_time = pd.to_datetime(timestamp, unit='ms').strftime('%H:%M:%S')
                    else:
                        trade_time = 'Unknown'
                except:
                    trade_time = 'Unknown'
                
                st.markdown(f"""
                <div style="background: var(--card-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0; border-left: 4px solid var(--accent-blue);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--text-primary); font-weight: 600;">{symbol}</span>
                        <span style="color: var(--text-secondary); font-size: 0.9rem;">{trade_time}</span>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        {side} • Qty: {qty} • Price: ${float(price):,.4f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    📊 No Real Trades Yet
                </h4>
                <p style="color: var(--text-secondary); margin: 0;">
                    Start real trading to see your trade history here.
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Simulated trading history
        if st.session_state['trades']:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                    📋 Simulated Trade History
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            trades_df = pd.DataFrame(st.session_state['trades'])
            if not trades_df.empty:
                trades_df = trades_df.tail(20)  # Show last 20 trades
                st.markdown(trades_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    📊 No Trades Yet
                </h4>
                <p style="color: var(--text-secondary); margin: 0;">
                    Start trading to see your trade history here.
                </p>
            </div>
            """, unsafe_allow_html=True)

with tabs[3]:
    try:
        tk = _exec.fetch_ticker(symbol)
        last = tk.get('last') or tk.get('close') or 0.0
        high24 = tk.get('high') or 0.0
        low24 = tk.get('low') or 0.0
        base_volume = tk.get('baseVolume') or 0.0
        quote_volume = tk.get('quoteVolume') or 0.0
        market_cap = tk.get('info', {}).get('marketCap') if isinstance(tk.get('info'), dict) else None
        
        def fmt_m(x):
            try:
                x = float(x)
                return f"${x/1_000_000:,.2f}M"
            except Exception:
                return "N/A"
        
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                📈 Market Data
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        colm1, colm2 = st.columns(2)
        with colm1:
            st.metric("Last Price", f"${float(last):,.4f}")
            st.metric("24h Change", f"{price_change_24h_pct:+.2f}%", f"{price_change_24h:+.4f}")
            st.metric("24h High", f"${float(high24):,.4f}")
            st.metric("24h Low", f"${float(low24):,.4f}")
        with colm2:
            st.metric("Base Vol (24h)", f"{float(base_volume):,.0f}")
            st.metric("Quote Vol (24h)", f"{float(quote_volume):,.0f}")
            st.metric("Market Cap", fmt_m(market_cap) if market_cap else "N/A")
    except Exception as e:
        st.error(f"Unable to fetch market data: {e}")

with tabs[4]:
    signal_now = bool(df['signal'].iat[-1]) if len(df) > 0 else False
    sig_badge = "BUY Signal Active" if signal_now else "No Signal"
    sig_color = "#48bb78" if signal_now else "#a0aec0"
    
    st.markdown(f"""
    <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                border: 1px solid var(--border-color);">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            🚨 Signal Status
        </h4>
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 1.5rem; font-weight: 700; color: {sig_color}; margin-bottom: 0.5rem;">
                {sig_badge}
            </div>
            <div style="color: var(--text-secondary); font-size: 0.9rem;">
                Last signal: {pd.Timestamp.now().strftime('%H:%M:%S')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tabs[5]:
    if st.session_state['arb_running']:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                🔍 Arbitrage Scanner
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Build simple exchanges map for scanner
            import ccxt
            ex_map = {}
            ex_map['binance'] = ccxt.binance()
            ex_map['bybit'] = ccxt.bybit()
            ex_map['mexc'] = ccxt.mexc()
            
            scanner = ArbitrageEngine(ex_map, [symbol], threshold_bps=10.0)
            opps = scanner.run_once()
            
            if opps:
                for o in opps:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                                border: 1px solid var(--border-color); margin-bottom: 0.5rem;">
                        <div style="color: var(--accent-green); font-weight: 600; margin-bottom: 0.5rem;">
                            💰 Arbitrage Opportunity
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.9rem;">
                            <strong>{o['symbol']}</strong><br/>
                            Buy on: {o['buy_on']}<br/>
                            Sell on: {o['sell_on']}<br/>
                            Spread: <span style="color: var(--accent-green); font-weight: 600;">{o['spread']*100:.2f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                            border: 1px solid var(--border-color); text-align: center;">
                    <div style="color: var(--text-secondary);">
                        🔍 No arbitrage opportunities found
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Arbitrage scanner error: {e}")
    else:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                🔍 Arbitrage Scanner
            </h4>
            <p style="color: var(--text-secondary); margin: 0;">
                Scanner is currently disabled. Enable it in the sidebar to start scanning for arbitrage opportunities.
            </p>
        </div>
        """, unsafe_allow_html=True)

with tabs[6]:
    # Order Management Tab
    st.markdown("""
    <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                border: 1px solid var(--border-color);">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            ⚙️ Order Management
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    if not paper and st.session_state['real_account_data'] and st.session_state['real_account_data'].get('orders'):
        # Real order management
        real_orders = st.session_state['real_account_data']['orders']
        if real_orders:
            st.markdown(f"**Open Orders ({len(real_orders)}):**")
            
            for order in real_orders:
                order_id = order.get('orderId', 'Unknown')
                symbol = order.get('symbol', 'Unknown')
                side = order.get('side', 'Unknown')
                qty = order.get('qty', 0)
                price = order.get('price', 0)
                status = order.get('orderStatus', 'Unknown')
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
                        <div style="color: var(--text-primary); font-weight: 600;">{symbol} • {side}</div>
                        <div style="color: var(--text-secondary); font-size: 0.9rem;">
                            Qty: {qty} • Price: ${float(price):,.4f} • Status: {status}
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.8rem;">
                            ID: {order_id}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_{order_id}"):
                        with st.spinner("Canceling order..."):
                            try:
                                result = _exec.cancel_order(order_id, symbol)
                                if result.get('status') != 'error':
                                    st.success(f"Order {order_id} canceled!")
                                    # Refresh account data
                                    account_data = _exec.get_account_info()
                                    st.session_state['real_account_data'] = account_data
                                    st.rerun()
                                else:
                                    st.error(f"Failed to cancel order: {result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error canceling order: {e}")
                
                with col3:
                    if st.button("🔄 Refresh", key=f"refresh_{order_id}"):
                        with st.spinner("Refreshing order data..."):
                            try:
                                account_data = _exec.get_account_info()
                                st.session_state['real_account_data'] = account_data
                                st.success("Order data refreshed!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error refreshing data: {e}")
        else:
            st.markdown("""
            <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📋 No Open Orders</h4>
                <p style="color: var(--text-secondary); margin: 0;">No orders to manage</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Paper trading or no real data
        if paper:
            st.markdown("""
            <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📝 Paper Trading Mode</h4>
                <p style="color: var(--text-secondary); margin: 0;">Order management not available in paper trading mode</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">🔐 Real Trading Required</h4>
                <p style="color: var(--text-secondary); margin: 0;">Enable real trading and fetch account data to manage orders</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Manual order placement (for advanced users)
    if not paper and st.session_state['account_validation'] and st.session_state['account_validation']['valid']:
        st.markdown("---")
        st.markdown("**Manual Order Placement:**")
        
        col1, col2 = st.columns(2)
        with col1:
            manual_symbol = st.text_input("Symbol", value=symbol, key="manual_symbol")
            manual_side = st.selectbox("Side", ["buy", "sell"], key="manual_side")
        with col2:
            manual_qty = st.number_input("Quantity", min_value=0.001, value=0.001, step=0.001, key="manual_qty")
            manual_leverage = st.number_input("Leverage", min_value=1, max_value=100, value=1, key="manual_leverage")
        
        if st.button("📤 Place Manual Order", key="place_manual_order"):
            if manual_symbol and manual_qty > 0:
                with st.spinner("Placing order..."):
                    try:
                        result = _exec.place_market_order(manual_symbol, manual_side, manual_qty, int(manual_leverage))
                        if result.get('status') != 'error':
                            st.success(f"Order placed successfully! ID: {result.get('id', 'Unknown')}")
                            # Refresh account data
                            account_data = _exec.get_account_info()
                            st.session_state['real_account_data'] = account_data
                            st.rerun()
                        else:
                            st.error(f"Failed to place order: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error placing order: {e}")
            else:
                st.error("Please fill in all required fields")

with tabs[7]:
    st.markdown('<div class="section-header">📊 Comprehensive Backtesting Metrics</div>', unsafe_allow_html=True)
    
    # Initialize metrics calculator
    metrics_calculator = ComprehensiveMetricsCalculator()

    # Optional: run backtest on demand when triggered from sidebar
    if st.session_state.get('backtest_trigger'):
        st.session_state['backtest_trigger'] = False
        with st.spinner("Running backtest with current settings..."):
            try:
                # Prepare data and signals for backtest
                df_bt = df.copy() if 'df' in locals() else None
                if df_bt is not None and not df_bt.empty:
                    # Ensure a boolean entry signal column exists
                    if 'signal' not in df_bt.columns:
                        # Fallback: generate weighted signals if available
                        try:
                            from indicators.weighted_signals import generate_weighted_signals
                            df_bt['signal'] = generate_weighted_signals(df_bt).astype(bool)
                        except Exception:
                            df_bt['signal'] = False
                    # Run enhanced backtest if available, else core
                    try:
                        from backtester.enhanced_backtester import run_enhanced_backtest
                        bt_res = run_enhanced_backtest(
                            df=df_bt,
                            entry_col='signal',
                            initial_cap=float(st.session_state.get('initial_capital', 10000.0)),
                            risk_per_trade=float(st.session_state.get('risk_per_trade', 0.01)),
                            stop_loss_pct=float(st.session_state.get('stop_loss_pct', 0.03)),
                            take_profit_pct1=float(st.session_state.get('take_profit_pct1', 0.03)),
                            take_profit_pct2=float(st.session_state.get('take_profit_pct2', 0.06)),
                            max_bars_in_trade=int(st.session_state.get('max_bars_in_trade', 100)),
                            fee_rate=0.0004,
                            daily_breaker_active=bool(st.session_state.get('daily_breaker_active', False)),
                            daily_pnl_limit=float(st.session_state.get('daily_loss_limit', -0.05)),
                        )
                    except Exception:
                        from backtester.core import run_backtest as run_basic_backtest
                        bt_res = run_basic_backtest(df_bt, entry_col='signal')

                    # Persist into session for metrics tab
                    st.session_state['trades'] = bt_res.get('trades', [])
                    st.session_state.setdefault('account', {'equity': []})
                    st.session_state['account']['equity'] = bt_res.get('df', {}).get('equity', []) if isinstance(bt_res.get('df'), dict) else (bt_res.get('df')['equity'].tolist() if bt_res.get('df') is not None and 'equity' in bt_res.get('df').columns else st.session_state['account'].get('equity', []))
                    st.success("Backtest completed. Open '📊 Comprehensive Backtesting Metrics' tab.")
                else:
                    st.warning("No market data available to backtest. Load data first.")
            except Exception as e:
                st.error(f"Backtest error: {e}")
    
    # Check if we have trading data
    if 'trades' in st.session_state and st.session_state['trades']:
        trades = st.session_state['trades']
        account = st.session_state.get('account', {'equity': [10000]})
        equity_curve = pd.Series(account['equity'])
        
        # Calculate comprehensive metrics
        with st.spinner("Calculating comprehensive metrics..."):
            try:
                metrics = metrics_calculator.calculate_comprehensive_metrics(
                    equity_curve=equity_curve,
                    trades=trades,
                    initial_capital=initial_cap,
                    risk_free_rate=0.02
                )
                
                # Display metrics report
                st.markdown("### 📈 Performance Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Return", f"{metrics.total_return:.2%}")
                    st.metric("Win Rate", f"{metrics.win_rate:.2%}")
                
                with col2:
                    st.metric("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
                    st.metric("Max Drawdown", f"{metrics.max_drawdown:.2%}")
                
                with col3:
                    st.metric("Profit Factor", f"{metrics.profit_factor:.2f}")
                    st.metric("Total Trades", f"{metrics.total_trades}")
                
                with col4:
                    st.metric("Calmar Ratio", f"{metrics.calmar_ratio:.2f}")
                    st.metric("Recovery Factor", f"{metrics.recovery_factor:.2f}")
                
                # Detailed metrics
                st.markdown("### 📋 Detailed Metrics")
                
                # Generate and display comprehensive report
                report = metrics_calculator.generate_comprehensive_report(metrics)
                st.text(report)
                
                # Export functionality
                st.markdown("### 💾 Export Metrics")
                if st.button("📥 Export Metrics to CSV"):
                    filename = f"backtest_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    metrics_calculator.export_metrics_to_csv(metrics, filename)
                    st.success(f"Metrics exported to {filename}")
                
            except Exception as e:
                st.error(f"Error calculating metrics: {str(e)}")
    else:
        st.info("No trading data available. Run some trades to see comprehensive metrics.")
    
    # Multi-timeframe analysis results
    if enable_mtf and 'mtf_analyzer' in locals():
        st.markdown("### 🔄 Multi-Timeframe Analysis Results")
        
        mtf_summary = mtf_analyzer.get_timeframe_summary()
        
        st.markdown(f"**Primary Timeframe:** {mtf_summary['primary_timeframe']}")
        st.markdown(f"**Total Timeframes:** {mtf_summary['total_timeframes']}")
        st.markdown(f"**Enabled Timeframes:** {mtf_summary['enabled_timeframes']}")
        
        # Display timeframe configurations
        tf_df = pd.DataFrame(mtf_summary['timeframes'])
        st.markdown("**Timeframe Configuration:**")
        st.markdown(tf_df.to_html(escape=False, index=False), unsafe_allow_html=True)

with tabs[8]:
    # Error Log Tab
    st.markdown("""
    <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                border: 1px solid var(--border-color);">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            🚨 Error Log & Diagnostics
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Error log controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**Recent Errors:**")
    
    with col2:
        if st.button("🔄 Refresh Log", key="refresh_error_log"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Log", key="clear_error_log"):
            error_handler.clear_errors()
            st.success("Error log cleared!")
            st.rerun()
    
    # Display recent errors
    recent_errors = error_handler.get_recent_errors(20)
    
    if recent_errors:
        st.markdown(f"**Showing {len(recent_errors)} recent errors:**")
        
        for error in reversed(recent_errors):  # Show newest first
            error_time = error['timestamp']
            error_type = error['type']
            error_message = error['message']
            error_id = error['id']
            
            # Color code by error type
            if "API" in error_type:
                color = "var(--accent-red)"
                icon = "🔌"
            elif "Validation" in error_type:
                color = "var(--accent-blue)"
                icon = "⚠️"
            elif "Trading" in error_type:
                color = "var(--accent-green)"
                icon = "📈"
            else:
                color = "var(--text-secondary)"
                icon = "❓"
            
            with st.expander(f"{icon} {error_type} - {error_time[:19]}", expanded=False):
                st.markdown(f"**Error ID:** `{error_id}`")
                st.markdown(f"**Message:** {error_message}")
                
                if error.get('context'):
                    st.markdown("**Context:**")
                    for key, value in error['context'].items():
                        st.markdown(f"• {key}: {value}")
                
                # Show traceback for debugging
                if st.checkbox("Show technical details", key=f"show_trace_{error_id}"):
                    st.code(error.get('traceback', 'No traceback available'), language='python')
    else:
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">✅ No Errors</h4>
            <p style="color: var(--text-secondary); margin: 0;">No errors have been logged recently</p>
        </div>
        """, unsafe_allow_html=True)
    
    # System diagnostics
    st.markdown("---")
    st.markdown("**System Diagnostics:**")
    
    # Check system status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Check if trading is active
        trading_status = "🟢 Active" if st.session_state.get('is_trading', False) else "🔴 Inactive"
        st.metric("Trading Status", trading_status)
    
    with col2:
        # Check account validation
        validation = st.session_state.get('account_validation')
        if validation and validation.get('valid'):
            validation_status = "🟢 Validated"
        elif validation:
            validation_status = "🔴 Failed"
        else:
            validation_status = "⚪ Not Checked"
        st.metric("Account Status", validation_status)
    
    with col3:
        # Check real account data
        real_data = st.session_state.get('real_account_data')
        if real_data and real_data.get('account_type') == 'real':
            data_status = "🟢 Real Data"
        elif real_data and real_data.get('account_type') == 'paper':
            data_status = "📝 Paper Data"
        else:
            data_status = "⚪ No Data"
        st.metric("Account Data", data_status)

st.markdown("</div>", unsafe_allow_html=True)

# Footer Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-top: 2rem; text-align: center;">
    <div style="color: var(--text-secondary); font-size: 0.9rem;">
        <p style="margin: 0; font-size: 0.8rem;">
            Developed by <strong style="color: var(--accent-blue);">Mushfiqur Rahaman</strong> • 
            Multi-Exchange Trading Platform v2.0
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-refresh logic
if st.session_state['is_trading']:
    time.sleep(int(refresh_secs))
    st.rerun()
