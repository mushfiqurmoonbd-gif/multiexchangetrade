# Multi-Exchange Trading — Developer README

🎯 **DUAL MODE TRADING PLATFORM — Paper + Real Trading**

> **Keep everything intact** — this README is written for developers: setup, environment, architecture, deployment, and developer notes.

---

## Copyright & License

**© 2025 Mushfiqur Rahman. All Rights Reserved.**
This software and documentation are proprietary and protected under international copyright laws.
No part of this project may be copied, modified, distributed, or used without the **explicit written consent** of the developer.

**Developer:** Mushfiqur Rahman
**Email:** [moonbd01717@gmail.com](mailto:moonbd01717@gmail.com)
**WhatsApp:** +8801701259687
**Telegram:** [@mushfiqmoon](https://t.me/mushfiqmoon)

Unauthorized use, reproduction, or distribution of this software is strictly prohibited and may result in legal action.

---

## Overview

A Multi-Exchange trading platform supporting both **Paper Trading** (simulated) and **Real Trading** (live orders across exchanges via CCXT). Intended for algorithmic trading, research, and quick deployment with a Streamlit dashboard.

**Core ideas:**

* Two modes: Paper Trading (safe simulated orders) and Real Trading (live, requires API keys).
* Multi-exchange connectivity (via CCXT) and multi-asset support: crypto + US stocks.
* Strategy manager picks strategies by market regime (trend/volatility).
* Background arbitrage engine monitors price gaps across exchanges.
* Extensive backtesting, logging, and export capabilities.

---

## Features

* 📝 **Paper Trading Mode** - Safe practice with simulated orders
* 🚀 **Real Trading Mode** - Live orders with real money (6 exchanges via CCXT)
* **Multi-Asset Support** - Trade cryptocurrencies and US stocks
* **Advanced Risk Management** - TP1/TP2/Runner system, daily breaker, configurable stop-loss
* **Weighted Indicators** - RSI (40%), WaveTrend (40%), Buy/Sell signals (20%)
* **Enhanced Backtesting** - 15+ timeframes, historical data, crypto + stocks
* **US Compliant Exchanges** - Alpaca, Coinbase, Kraken
* **Strategies**: EMA crossover, RSI + Bollinger (mean reversion), Grid trading
* **Strategy Manager** - Selects a strategy by market regime (trend/volatility)
* **Arbitrage engine** (background) checks price gaps across exchanges
* **Risk**: position sizing, SL/TP, capital allocation
* **Backtester and metrics; CSV export**
* **Comprehensive logging of all trades and PnL**

---

## Quick Start (development)

1. Clone the repo:

```bash
git clone <repo-url>
cd <repo-folder>
```

2. Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate    # macOS / Linux
.\.venv\Scripts\activate   # Windows PowerShell
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` (REQUIRED for Real Trading). See **Environment Variables** below.

5. Run the dashboard locally:

```bash
python -m streamlit run app.py
```

> The Streamlit dashboard exposes controls to switch between Paper and Real modes, change strategy parameters, and view logs/backtest results.

---

## Environment Variables (.env)

**Required for Real Trading (live orders):**

```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
MEXC_API_KEY=your_api_key
MEXC_API_SECRET=your_api_secret
ALPACA_API_KEY=your_api_key         # for US stocks & crypto
ALPACA_API_SECRET=your_api_secret
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
COINBASE_PASSPHRASE=your_passphrase
KRAKEN_API_KEY=your_api_key         # US compliant crypto
KRAKEN_API_SECRET=your_api_secret
```

**Notes:**

* Keep this file out of version control. Add `.env` to `.gitignore`.
* Only enable real trading after you’ve thoroughly tested strategies in Paper mode.

---

## Exchanges Supported (via CCXT)

* Binance
* Bybit
* MEXC
* Coinbase (pro-style API)
* Alpaca (US stocks & crypto)
* Kraken

> Additional exchanges can be added by adding configs and mapping CCXT exchange names/providers.

---

## Modes

### Paper Trading Mode

* Uses real market data streams but simulates order execution and PnL.
* Useful for strategy development, parameter tuning, and performance validation.
* No real money at risk.

### Real Trading Mode

* Sends orders to exchanges using API keys.
* **REAL MONEY AT RISK** — only enable with valid keys and after risk checks.
* Monitor positions and logs closely.

---

## Strategies & Strategy Manager

**Built-in strategies:**

* EMA crossover
* RSI + Bollinger (mean reversion)
* Grid trading

**Strategy Manager:**

* Monitors market regime (trend vs volatility) and chooses the most suitable strategy.
* Can be extended to include additional regime detection methods and models.

---

## Indicators & Signal Weighting

* RSI — weight 40%
* WaveTrend — weight 40%
* Buy/Sell signals (other sources) — weight 20%

Signals are combined via weighted voting to generate entry/exit decisions.

---

## Risk Management

* Position sizing rules (configurable)
* Stop-loss (configurable)
* Take-profits: TP1 / TP2 / Runner system
* Daily breaker to stop trading after daily loss threshold
* Capital allocation logic across exchanges and instruments

---

## Arbitrage Engine

* Background process that checks price gaps across exchanges
* Designed to identify temporary inefficiencies and notify or execute arb strategies
* Runs continuously with throttling and rate-limit aware calls to CCXT

---

## Backtester

* Supports 15+ timeframes and both crypto & stocks historical data
* Outputs common metrics (Sharpe, Win rate, Max drawdown, CAGR, etc.)
* CSV export available for research and record-keeping

---

## Logging & Persistence

* Comprehensive logging of all trades, order events, and PnL
* Persist logs to local storage (CSV / Parquet) and optionally a database
* Recommended: use a dedicated time-series DB or Postgres for production

---

## Deployment (Render — one-click recommended)

**Files to ensure exist in repo root:**

* `render.yaml`
* `.streamlit/config.toml`

**Render blueprint / deploy steps:**

1. Create Render service (Web Service)
2. Choose `Blueprint` and link this repository
3. Render will:

   * Install dependencies: `pip install -r requirements.txt`
   * Start: `python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Provide required environment variables on the Render dashboard (only enable REAL keys if absolutely sure)

**Security note:** Never commit API keys. Use Render's environment variable secrets.


## Developer Notes

* Use feature flags to safely enable/disable live order execution.
* Put any heavy background tasks (arbitrage, continuous backfill) into separate worker processes or scheduled jobs.
* Be mindful of rate limits for each exchange. Use CCXT rate-limit helpers and implement retry/backoff.
* Add simulation of slippage and realistic fees in Paper Trading to better reflect live conditions.
* Add CI checks for style and unit tests. Integration tests that mock CCXT are recommended.

---

## Safety & Compliance

* **WARNING:** Real Trading mode uses real money. The platform does not guarantee profits.
* Make sure you comply with local laws and exchange policies when trading securities and crypto.
* For US residents, ensure trading on US regulated exchanges adheres to applicable rules.

---

## Extending the Project

* Add more indicators and ML-driven regime detection
* Add support for additional exchanges
* Add a microservice architecture for execution vs analytics
* Add user authentication and multi-user support (if exposing real trading)

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and linters
4. Submit a PR with a clear description and test coverage

---

## License

**Proprietary License — All Rights Reserved**
This software is protected by copyright © 2025 **Mushfiqur Rahman**.
Unauthorized copying, modification, or distribution of this software, via any medium, is strictly prohibited without written consent.
For commercial or research inquiries, contact:

* **Email:** [moonbd01717@gmail.com](mailto:moonbd01717@gmail.com)
* **WhatsApp:** +8801701259687
* **Telegram:** [@mushfiqmoon](https://t.me/mushfiqmoon)

---

*Prepared and protected by Mushfiqur Rahman — developer and copyright holder.*
