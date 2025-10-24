import pandas as pd
import requests
from typing import List, Dict, Any
from datetime import datetime

class BybitV5DataFetcher:
    def __init__(self, paper: bool = True, trading_type: str = "spot"):
        self.paper = paper
        self.trading_type = trading_type.lower()
        
        # Set base URL based on trading mode
        if paper:
            self.base_url = "https://api-testnet.bybit.com"
            print("Bybit V5 Testnet Data Fetcher - Paper Trading")
        else:
            self.base_url = "https://api.bybit.com"
            print("Bybit V5 Mainnet Data Fetcher - Real Trading")
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make request to Bybit v5 API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Bybit Data Fetch Error: {e}")
            return {"error": str(e), "success": False}
    
    def get_symbols(self, quote_filter: str = "USDT") -> List[str]:
        """Get available trading symbols"""
        endpoint = "/v5/market/instruments-info"
        params = {"category": self.trading_type}
        
        response = self._make_request(endpoint, params)
        
        if response.get("retCode") != 0:
            print(f"Bybit V5 API Error getting symbols: {response.get('retMsg', 'Unknown error')}")
            return []
        
        symbols = []
        for item in response.get("result", {}).get("list", []):
            symbol = item.get("symbol", "")
            if symbol and symbol.endswith(quote_filter):
                symbols.append(symbol)
        
        print(f"Found {len(symbols)} {quote_filter} symbols on Bybit V5 {self.trading_type}")
        return sorted(symbols)
    
    def get_timeframes(self) -> List[str]:
        """Get available timeframes"""
        # Bybit v5 standard timeframes
        return ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"]
    
    def get_ohlcv_data(self, symbol: str, timeframe: str = "60", limit: int = 500) -> pd.DataFrame:
        """Get OHLCV data and convert to DataFrame"""
        endpoint = "/v5/market/kline"
        
        # Map common timeframes to Bybit V5 format
        timeframe_map = {
            "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
            "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720",
            "1d": "D", "1w": "W", "1M": "M"
        }
        
        # Convert timeframe if needed
        bybit_timeframe = timeframe_map.get(timeframe, timeframe)
        
        params = {
            "category": self.trading_type,
            "symbol": symbol,
            "interval": bybit_timeframe,
            "limit": str(limit)
        }
        
        response = self._make_request(endpoint, params)
        
        # Check if request was successful (Bybit V5 uses retCode instead of success)
        if response.get("retCode") != 0:
            print(f"Bybit V5 API Error: {response.get('retMsg', 'Unknown error')}")
            return pd.DataFrame()
        
        klines = response.get("result", {}).get("list", [])
        
        if not klines:
            print(f"No kline data received for {symbol}")
            return pd.DataFrame()
        
        # Bybit V5 returns data in reverse chronological order (newest first)
        # We need to reverse it to get oldest first
        klines = list(reversed(klines))
        
        # Convert to DataFrame - Bybit V5 format: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
        df = pd.DataFrame(klines, columns=[
            'start_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Convert data types
        df['timestamp'] = pd.to_datetime(pd.to_numeric(df['start_time']), unit='ms')
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['turnover'] = pd.to_numeric(df['turnover'])
        
        # Sort by timestamp to ensure chronological order
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Return only the required columns
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    def get_ticker_data(self, symbol: str) -> dict:
        """Get latest ticker data"""
        endpoint = "/v5/market/tickers"
        params = {
            "category": self.trading_type,
            "symbol": symbol
        }
        
        response = self._make_request(endpoint, params)
        
        # Bybit V5 uses retCode instead of success
        if response.get("retCode") != 0:
            print(f"Bybit V5 API Error: {response.get('retMsg', 'Unknown error')}")
            return {}
        
        tickers = response.get("result", {}).get("list", [])
        if not tickers:
            return {}
        
        return tickers[0]  # Return first (and usually only) ticker
    
    def get_server_time(self) -> int:
        """Get server timestamp"""
        endpoint = "/v5/market/time"
        response = self._make_request(endpoint)
        
        if response.get("retCode") == 0:
            return int(response.get("result", {}).get("timeSecond", 0))
        
        return int(time.time())
    
    def get_funding_rate(self, symbol: str) -> dict:
        """Get funding rate for futures"""
        if self.trading_type not in ["linear", "inverse"]:
            return {}
        
        endpoint = "/v5/market/funding/history"
        params = {
            "category": self.trading_type,
            "symbol": symbol,
            "limit": "1"
        }
        
        response = self._make_request(endpoint, params)
        
        if not response.get("success", False):
            return {}
        
        funding_data = response.get("result", {}).get("list", [])
        if not funding_data:
            return {}
        
        return funding_data[0]
    
    def get_open_interest(self, symbol: str) -> dict:
        """Get open interest for futures"""
        if self.trading_type not in ["linear", "inverse"]:
            return {}
        
        endpoint = "/v5/market/open-interest"
        params = {
            "category": self.trading_type,
            "symbol": symbol,
            "intervalTime": "5min",
            "limit": "1"
        }
        
        response = self._make_request(endpoint, params)
        
        if not response.get("success", False):
            return {}
        
        oi_data = response.get("result", {}).get("list", [])
        if not oi_data:
            return {}
        
        return oi_data[0]
