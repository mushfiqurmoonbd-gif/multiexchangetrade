# Multi-Exchange Trading — Paper + Real Trading

🎯 **DUAL MODE TRADING PLATFORM** 🎯

Features
- **📝 Paper Trading Mode** - Safe practice with simulated orders
- **🚀 Real Trading Mode** - Live orders with real money (6 exchanges via CCXT)
- **Multi-Asset Support** - Trade cryptocurrencies and US stocks
- **Advanced Risk Management** - TP1/TP2/Runner system, daily breaker, configurable stop-loss
- **Weighted Indicators** - RSI (40%), WaveTrend (40%), Buy/Sell signals (20%)
- **Enhanced Backtesting** - 15+ timeframes, historical data, crypto + stocks
- **US Compliant Exchanges** - Alpaca, Coinbase, Kraken
- Strategies: EMA crossover, RSI + Bollinger (mean reversion), Grid trading
- Strategy Manager selects a strategy by market regime (trend/volatility)
- Arbitrage engine (background) checks price gaps across exchanges
- Risk: position sizing, SL/TP, capital allocation
- Backtester and metrics; CSV export
- **Comprehensive logging** of all trades and PnL

Quick Start
1) Install deps
   - `pip install -r requirements.txt`
2) Set environment (.env) - **Required for Real Trading**
   - `BINANCE_API_KEY=your_api_key`
   - `BINANCE_API_SECRET=your_api_secret`
   - `BYBIT_API_KEY=your_api_key`
   - `BYBIT_API_SECRET=your_api_secret`
   - `MEXC_API_KEY=your_api_key`
   - `MEXC_API_SECRET=your_api_secret`
   - `ALPACA_API_KEY=your_api_key` (for US stocks & crypto)
   - `ALPACA_API_SECRET=your_api_secret`
   - `COINBASE_API_KEY=your_api_key`
   - `COINBASE_API_SECRET=your_api_secret`
   - `COINBASE_PASSPHRASE=your_passphrase`
   - `KRAKEN_API_KEY=your_api_key` (US compliant crypto)
   - `KRAKEN_API_SECRET=your_api_secret`
3) Run dashboard (local)
   - `python -m streamlit run app.py`

Deploy to Render (one-click)
- Ensure these files exist:
  - `render.yaml`
  - `.streamlit/config.toml`
- On Render, choose “Blueprint” and point to this repo. It will:
  - Install deps: `pip install -r requirements.txt`
  - Start: `python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
  - Expose a public URL automatically

**📝 Paper Trading Mode**
- Safe practice environment
- No real money at risk
- Real market data for realistic testing
- Perfect for strategy development

**🚀 Real Trading Mode**
- **REAL MONEY AT RISK** - Places actual orders
- Requires valid API keys
- Monitor positions closely
- Use proper risk management settings
