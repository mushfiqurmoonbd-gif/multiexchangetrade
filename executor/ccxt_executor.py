import os
import time
from typing import List, Dict, Any
import pandas as pd
import ccxt
from dotenv import load_dotenv
from .bybit_v5_executor import BybitV5Executor
from .bybit_v5_data_fetcher import BybitV5DataFetcher
load_dotenv()

class CCXTExecutor:
    def __init__(self, exchange_name: str, api_key: str = None, api_secret: str = None, paper=True, fee_rate: float = 0.0004, trading_type: str = "spot"):
        self.paper = paper
        self.exchange_name = exchange_name
        self.trading_type = trading_type.lower()  # "spot" or "futures"
        self.fee_rate = float(fee_rate)
        exchange_cls = getattr(ccxt, exchange_name)
        kwargs = {}
        if api_key and api_secret:
            kwargs.update({'apiKey': api_key, 'secret': api_secret})
        
        # instantiate exchange with proper initialization
        try:
            self.ex = exchange_cls(kwargs) if kwargs else exchange_cls()
        except TypeError:
            # Fallback for different CCXT versions
            self.ex = exchange_cls()
            if api_key and api_secret:
                self.ex.apiKey = api_key
                self.ex.secret = api_secret
        
        # Use Bybit v5 for Bybit exchange
        if exchange_name.lower() == 'bybit':
            self.bybit_v5 = BybitV5Executor(api_key, api_secret, paper, trading_type)
            self.bybit_data = BybitV5DataFetcher(paper, trading_type)
            print(f"Using Bybit V5 API - {trading_type.upper()} mode")
        else:
            # Use CCXT for other exchanges
            self._configure_exchange()
        
        self.markets_loaded = False

    def _configure_exchange(self):
        """Configure exchange-specific settings"""
        try:
            self.ex.enableRateLimit = True
            self.ex.timeout = max(getattr(self.ex, 'timeout', 10000), 20000)
            
            # Exchange-specific configurations
            self.ex.options = getattr(self.ex, 'options', {})
            
            if self.exchange_name.lower() == 'binance':
                # Binance specific settings
                if self.trading_type == 'futures':
                    self.ex.options['defaultType'] = 'future'  # Futures trading
                    self.ex.options['sandbox'] = self.paper  # Use sandbox for paper trading
                else:
                    self.ex.options['defaultType'] = 'spot'  # Spot trading
            elif self.exchange_name.lower() == 'bybit':
                # Bybit specific settings
                if self.trading_type == 'futures':
                    self.ex.options['defaultType'] = 'contract'  # Futures trading
                else:
                    self.ex.options['defaultType'] = 'spot'  # Spot trading
            elif self.exchange_name.lower() == 'mexc':
                # MEXC specific settings
                if self.trading_type == 'futures':
                    self.ex.options['defaultType'] = 'future'  # Futures trading
                else:
                    self.ex.options['defaultType'] = 'spot'  # Spot trading
            elif self.exchange_name.lower() == 'alpaca':
                # Alpaca specific settings (US stocks and crypto)
                self.ex.options['sandbox'] = self.paper  # Use paper trading for sandbox
                if not self.paper:
                    # For live trading, ensure we're using the live API
                    self.ex.options['baseUrl'] = 'https://api.alpaca.markets'
                else:
                    # For paper trading, use the paper API
                    self.ex.options['baseUrl'] = 'https://paper-api.alpaca.markets'
            elif self.exchange_name.lower() == 'coinbase':
                # Coinbase Pro specific settings
                self.ex.options['sandbox'] = self.paper  # Use sandbox for paper trading
                if self.paper:
                    self.ex.options['baseUrl'] = 'https://api-public.sandbox.pro.coinbase.com'
                else:
                    self.ex.options['baseUrl'] = 'https://api.pro.coinbase.com'
            elif self.exchange_name.lower() == 'kraken':
                # Kraken specific settings (US compliant)
                self.ex.options['sandbox'] = self.paper
                if self.paper:
                    self.ex.options['baseUrl'] = 'https://api-sandbox.kraken.com'
                else:
                    self.ex.options['baseUrl'] = 'https://api.kraken.com'
                
            print(f"{self.exchange_name.upper()} {self.trading_type.upper()} exchange configured successfully")
        except Exception as e:
            print(f"Warning: Could not configure {self.exchange_name}: {e}")
            pass

    def load_markets(self):
        if not self.markets_loaded:
            try:
                self.ex.load_markets()
                self.markets_loaded = True
            except Exception:
                # leave markets_loaded False; callers should handle empty lists
                self.markets_loaded = False

    def list_symbols(self, quote_filter: str = 'USDT') -> List[str]:
        if self.exchange_name.lower() == 'bybit':
            # Use Bybit v5 data fetcher
            symbols = self.bybit_data.get_symbols(quote_filter)
            
            # If Bybit v5 fails, fallback to CCXT
            if not symbols:
                print(f"Bybit V5 symbol fetch failed, trying CCXT fallback...")
                try:
                    self.load_markets()
                    symbols = list(self.ex.markets.keys()) if getattr(self.ex, 'markets', None) else []
                    if quote_filter:
                        symbols = [s for s in symbols if s.endswith(f"/{quote_filter}")]
                    symbols = sorted(symbols)
                    print(f"CCXT fallback found {len(symbols)} symbols")
                except Exception as e:
                    print(f"CCXT fallback also failed: {e}")
                    return []
            
            return symbols
        
        try:
            self.load_markets()
            symbols = list(self.ex.markets.keys()) if getattr(self.ex, 'markets', None) else []
            if quote_filter:
                symbols = [s for s in symbols if s.endswith(f"/{quote_filter}")]
            return sorted(symbols)
        except Exception:
            return []

    def list_timeframes(self) -> List[str]:
        if self.exchange_name.lower() == 'bybit':
            # Use Bybit v5 timeframes
            return self.bybit_data.get_timeframes()
        
        try:
            tfs = getattr(self.ex, 'timeframes', None)
            if isinstance(tfs, dict) and tfs:
                return list(tfs.keys())
        except Exception:
            pass
        return ['1m','3m','5m','15m','30m','1h','2h','4h','1d']

    def fetch_ohlcv_df(self, symbol: str, timeframe: str = '1h', limit: int = 500) -> pd.DataFrame:
        if self.exchange_name.lower() == 'bybit':
            # Use Bybit v5 data fetcher
            df = self.bybit_data.get_ohlcv_data(symbol, timeframe, limit)
            
            # If Bybit v5 fails, fallback to CCXT
            if df.empty:
                print(f"Bybit V5 data fetch failed for {symbol}, trying CCXT fallback...")
                try:
                    ohlcv = self.ex.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
                    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    print(f"CCXT fallback successful for {symbol}")
                except Exception as e:
                    print(f"CCXT fallback also failed for {symbol}: {e}")
                    return pd.DataFrame()
            
            return df
        
        ohlcv = self.ex.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        # CCXT: [ timestamp, open, high, low, close, volume ]
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def fetch_price(self, symbol: str) -> float:
        if self.exchange_name.lower() == 'bybit':
            # Use Bybit v5 data fetcher
            ticker = self.bybit_data.get_ticker_data(symbol)
            return float(ticker.get('lastPrice', 0.0))
        
        try:
            t = self.ex.fetch_ticker(symbol)
            return float(t.get('last') or t.get('close') or 0.0)
        except Exception:
            return 0.0

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        if self.exchange_name.lower() == 'bybit':
            # Use Bybit v5 data fetcher
            return self.bybit_data.get_ticker_data(symbol)
        
        try:
            return self.ex.fetch_ticker(symbol)
        except Exception:
            return {}
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """Fetch OHLCV data for a symbol"""
        if self.exchange_name.lower() == 'bybit':
            # Use Bybit v5 data fetcher
            df = self.bybit_data.get_ohlcv_data(symbol, timeframe, limit)
            if df is not None and not df.empty:
                # Convert DataFrame to CCXT format: [timestamp, open, high, low, close, volume]
                ohlcv = []
                for _, row in df.iterrows():
                    ohlcv.append([
                        int(row['timestamp'].timestamp() * 1000),  # timestamp in ms
                        float(row['open']),
                        float(row['high']),
                        float(row['low']),
                        float(row['close']),
                        float(row['volume'])
                    ])
                return ohlcv
            return []
        
        try:
            return self.ex.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            print(f"Error fetching OHLCV from {self.exchange_name}: {e}")
            return []

    def place_market_order(self, symbol: str, side: str, amount: float, leverage: int = 1, margin_mode: str = "isolated"):
        # sanitize amount to exchange precision/limits
        amount = self.sanitize_amount(symbol, amount)
        if amount <= 0:
            return {'status': 'skipped', 'reason': 'amount_too_small', 'symbol': symbol}
        
        if self.exchange_name.lower() == 'bybit':
            # Use Bybit v5 executor
            return self.bybit_v5.place_market_order(symbol, side, amount, leverage)
        
        if self.paper:
            # Paper Trading Mode - Safe simulation
            order_type = "FUTURES" if self.trading_type == "futures" else "SPOT"
            print(f"PAPER_ORDER: {side} {amount} {symbol} on {self.exchange_name.upper()} {order_type} - SIMULATED ORDER")
            return {
                'status': 'paper', 
                'symbol': symbol, 
                'side': side, 
                'amount': amount, 
                'exchange': self.exchange_name,
                'trading_type': self.trading_type,
                'leverage': leverage if self.trading_type == "futures" else 1,
                'margin_mode': margin_mode if self.trading_type == "futures" else None,
                'ts': int(time.time()*1000),
                'id': f"paper_{int(time.time()*1000)}"
            }
        else:
            # Real Trading Mode - Live orders
            try:
                order_type = "FUTURES" if self.trading_type == "futures" else "SPOT"
                print(f"REAL_ORDER: {side} {amount} {symbol} on {self.exchange_name.upper()} {order_type} - Executing trade")
                
                if self.trading_type == "futures":
                    # Futures-specific order parameters
                    order_params = {
                        'symbol': symbol,
                        'side': side,
                        'amount': amount,
                        'type': 'market'
                    }
                    # Add leverage and margin mode for futures
                    if hasattr(self.ex, 'set_leverage'):
                        self.ex.set_leverage(leverage, symbol)
                    if hasattr(self.ex, 'set_margin_mode'):
                        self.ex.set_margin_mode(margin_mode, symbol)
                else:
                    # Spot trading
                    order_params = {
                        'symbol': symbol,
                        'side': side,
                        'amount': amount,
                        'type': 'market'
                    }
                
                order = self.ex.create_market_order(**order_params)
                print(f"ORDER_PLACED on {self.exchange_name.upper()} {order_type}: {order}")
                return order
            except Exception as e:
                print(f"ORDER_ERROR on {self.exchange_name.upper()}: {e}")
                return {'status': 'error', 'symbol': symbol, 'side': side, 'amount': amount, 'exchange': self.exchange_name, 'trading_type': self.trading_type, 'error': str(e)}

    def fetch_balance(self) -> dict:
        """Fetch real account balance from exchange"""
        if self.paper:
            # Return mock balance for paper trading
            return {
                'USDT': {
                    'free': 10000.0,
                    'used': 0.0,
                    'total': 10000.0
                }
            }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.exchange_name.lower() == 'bybit':
                    # Use Bybit v5 executor
                    balance_data = self.bybit_v5.get_account_balance()
                    if balance_data.get('retCode') == 0:
                        # Parse Bybit v5 balance format
                        result = balance_data.get('result', {})
                        list_data = result.get('list', [])
                        if list_data:
                            coins = list_data[0].get('coin', [])
                            balance = {}
                            for coin in coins:
                                coin_name = coin.get('coin', '')
                                wallet_balance = float(coin.get('walletBalance', 0))
                                # Handle empty string for availableToWithdraw
                                available_str = coin.get('availableToWithdraw', '0')
                                available = float(available_str) if available_str else 0.0
                                balance[coin_name] = {
                                    'free': available,
                                    'used': wallet_balance - available,
                                    'total': wallet_balance
                                }
                            return balance
                    elif balance_data.get('retCode') != 0:
                        error_msg = balance_data.get('retMsg', 'Unknown error')
                        raise Exception(f"Bybit API error: {error_msg}")
                    return {}
                else:
                    # Use CCXT for other exchanges
                    return self.ex.fetch_balance()
            except Exception as e:
                print(f"Error fetching balance from {self.exchange_name} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    print(f"Failed to fetch balance after {max_retries} attempts")
                    return {}
                time.sleep(1)  # Wait before retry
        return {}

    def fetch_positions(self, symbol: str = None) -> list:
        """Fetch real positions from exchange"""
        if self.paper:
            return []
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.exchange_name.lower() == 'bybit':
                    # Use Bybit v5 executor
                    positions_data = self.bybit_v5.get_positions(symbol)
                    if positions_data.get('success'):
                        return positions_data.get('result', {}).get('list', [])
                    elif positions_data.get('error'):
                        raise Exception(f"Bybit API error: {positions_data['error']}")
                    return []
                else:
                    # Use CCXT for other exchanges
                    return self.ex.fetch_positions(symbol)
            except Exception as e:
                print(f"Error fetching positions from {self.exchange_name} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    print(f"Failed to fetch positions after {max_retries} attempts")
                    return []
                time.sleep(1)  # Wait before retry
        return []

    def fetch_orders(self, symbol: str = None, limit: int = 100) -> list:
        """Fetch real order history from exchange"""
        if self.paper:
            return []
        
        try:
            if self.exchange_name.lower() == 'bybit':
                # Use Bybit v5 executor
                orders_data = self.bybit_v5.get_open_orders(symbol)
                if orders_data.get('success'):
                    return orders_data.get('result', {}).get('list', [])
                return []
            else:
                # Use CCXT for other exchanges
                return self.ex.fetch_orders(symbol, limit=limit)
        except Exception as e:
            print(f"Error fetching orders from {self.exchange_name}: {e}")
            return []

    def fetch_trades(self, symbol: str = None, limit: int = 100) -> list:
        """Fetch real trading history from exchange"""
        if self.paper:
            return []
        
        try:
            if self.exchange_name.lower() == 'bybit':
                # Use Bybit v5 executor
                trades_data = self.bybit_v5.get_trading_history(symbol, limit)
                if trades_data.get('success'):
                    return trades_data.get('result', {}).get('list', [])
                return []
            else:
                # Use CCXT for other exchanges
                return self.ex.fetch_my_trades(symbol, limit=limit)
        except Exception as e:
            print(f"Error fetching trades from {self.exchange_name}: {e}")
            return []

    def cancel_order(self, order_id: str, symbol: str = None) -> dict:
        """Cancel an order"""
        if self.paper:
            print(f"PAPER_CANCEL: Order {order_id} on {self.exchange_name.upper()} - SIMULATED")
            return {'status': 'paper', 'id': order_id, 'symbol': symbol}
        
        try:
            if self.exchange_name.lower() == 'bybit':
                # Use Bybit v5 executor
                return self.bybit_v5.cancel_order(symbol, order_id)
            else:
                # Use CCXT for other exchanges
                return self.ex.cancel_order(order_id, symbol)
        except Exception as e:
            print(f"Error canceling order {order_id} on {self.exchange_name}: {e}")
            return {'status': 'error', 'error': str(e)}

    def get_account_info(self) -> dict:
        """Get comprehensive account information"""
        if self.paper:
            return {
                'balance': self.fetch_balance(),
                'positions': [],
                'orders': [],
                'trades': [],
                'account_type': 'paper'
            }
        
        try:
            return {
                'balance': self.fetch_balance(),
                'positions': self.fetch_positions(),
                'orders': self.fetch_orders(),
                'trades': self.fetch_trades(),
                'account_type': 'real'
            }
        except Exception as e:
            print(f"Error fetching account info from {self.exchange_name}: {e}")
            return {
                'balance': {},
                'positions': [],
                'orders': [],
                'trades': [],
                'account_type': 'error',
                'error': str(e)
            }

    def validate_account(self) -> dict:
        """Validate account access and permissions"""
        if self.paper:
            return {
                'valid': True,
                'message': 'Paper trading mode - no validation needed',
                'balance_available': True,
                'trading_enabled': True
            }
        
        try:
            # Test balance access
            balance = self.fetch_balance()
            balance_available = bool(balance)
            
            # Test market data access
            ticker = self.fetch_ticker('BTC/USDT' if self.exchange_name.lower() != 'bybit' else 'BTCUSDT')
            market_data_available = bool(ticker)
            
            return {
                'valid': balance_available and market_data_available,
                'message': 'Account validation successful' if balance_available and market_data_available else 'Account validation failed',
                'balance_available': balance_available,
                'trading_enabled': balance_available,
                'market_data_available': market_data_available
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Account validation failed: {e}',
                'balance_available': False,
                'trading_enabled': False,
                'error': str(e)
            }

    def close(self):
        pass

    # -------- Precision / Limits helpers --------
    def get_market(self, symbol: str) -> Dict[str, Any]:
        try:
            self.load_markets()
            return self.ex.market(symbol)
        except Exception:
            return {}

    def sanitize_amount(self, symbol: str, amount: float) -> float:
        try:
            m = self.get_market(symbol)
            precision = m.get('precision', {}).get('amount') if m else None
            min_amt = m.get('limits', {}).get('amount', {}).get('min') if m else None
            max_amt = m.get('limits', {}).get('amount', {}).get('max') if m else None
            amt = float(amount)
            if precision is not None:
                step = 10 ** (-precision)
                amt = (int(amt / step)) * step
            if min_amt is not None and amt < float(min_amt):
                return 0.0
            if max_amt is not None and amt > float(max_amt):
                amt = float(max_amt)
            return max(0.0, amt)
        except Exception:
            return max(0.0, float(amount))
