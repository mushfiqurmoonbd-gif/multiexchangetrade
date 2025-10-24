import os
import time
import hmac
import hashlib
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

class BybitV5Executor:
    def __init__(self, api_key: str = None, api_secret: str = None, paper: bool = True, trading_type: str = "spot"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper
        self.trading_type = trading_type.lower()
        
        # Set base URLs based on trading mode
        if paper:
            self.base_url = "https://api-testnet.bybit.com"
            self.ws_url = "wss://stream-testnet.bybit.com/v5/public/spot"
            print("Bybit V5 Testnet Mode - Paper Trading")
        else:
            self.base_url = "https://api.bybit.com"
            self.ws_url = "wss://stream.bybit.com/v5/public/spot"
            print("Bybit V5 Mainnet Mode - Real Trading")
    
    def _generate_signature(self, params: dict, timestamp: str) -> str:
        """Generate HMAC SHA256 signature for Bybit v5 API"""
        if not self.api_secret:
            return ""
        
        # Create query string for parameters only (not including api_key and timestamp)
        query = "&".join([f"{k}={v}" for k, v in params.items()]) if params else ""
        
        # Create the string to sign: timestamp + api_key + recv_window + query
        recv_window = "5000"
        sign_string = timestamp + self.api_key + recv_window + query
        
        # Generate signature
        signature = hmac.new(
            self.api_secret.encode(),
            sign_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_headers(self, params: dict = None) -> dict:
        """Generate headers for authenticated requests"""
        if not self.api_key or not self.api_secret:
            return {}
        
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(params or {}, timestamp)
        
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": "5000",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
        """Make authenticated request to Bybit v5 API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(params)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Bybit API Error: {e}")
            return {"error": str(e), "success": False}
    
    def get_account_balance(self, account_type: str = "UNIFIED") -> dict:
        """Get account balance"""
        endpoint = "/v5/account/wallet-balance"
        params = {
            "accountType": account_type,
            "coin": "USDT"
        }
        
        if self.paper:
            # For paper trading, return mock balance
            return {
                "result": {
                    "list": [{
                        "accountType": account_type,
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "10000.00000000",
                            "availableToWithdraw": "10000.00000000"
                        }]
                    }]
                },
                "success": True
            }
        
        return self._make_request("GET", endpoint, params)
    
    def get_ticker(self, symbol: str) -> dict:
        """Get latest ticker price"""
        endpoint = "/v5/market/tickers"
        params = {
            "category": self.trading_type,
            "symbol": symbol
        }
        
        return self._make_request("GET", endpoint, params)
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 500) -> dict:
        """Get historical kline data"""
        endpoint = "/v5/market/kline"
        params = {
            "category": self.trading_type,
            "symbol": symbol,
            "interval": interval,
            "limit": str(limit)
        }
        
        return self._make_request("GET", endpoint, params)
    
    def place_market_order(self, symbol: str, side: str, qty: float, leverage: int = 1) -> dict:
        """Place a market order"""
        if self.paper:
            # Paper trading - return mock order
            order_id = f"paper_{int(time.time() * 1000)}"
            print(f"PAPER_ORDER: {side} {qty} {symbol} on Bybit V5 Testnet - SIMULATED ORDER")
            return {
                "result": {
                    "orderId": order_id,
                    "orderLinkId": f"paper_{order_id}",
                    "symbol": symbol,
                    "side": side,
                    "orderType": "Market",
                    "qty": str(qty),
                    "price": "0",
                    "leverage": str(leverage),
                    "category": self.trading_type,
                    "orderStatus": "Filled",
                    "timeInForce": "IOC",
                    "createTime": str(int(time.time() * 1000))
                },
                "success": True
            }
        
        # Real trading
        endpoint = "/v5/order/create"
        data = {
            "category": self.trading_type,
            "symbol": symbol,
            "side": side,
            "orderType": "Market",
            "qty": str(qty),
            "timeInForce": "IOC"
        }
        
        # Add leverage for futures
        if self.trading_type in ["linear", "inverse"]:
            data["leverage"] = str(leverage)
        
        print(f"REAL_ORDER: {side} {qty} {symbol} on Bybit V5 Mainnet - Executing trade")
        return self._make_request("POST", endpoint, data=data)
    
    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """Cancel an order"""
        if self.paper:
            print(f"PAPER_CANCEL: Order {order_id} on Bybit V5 Testnet - SIMULATED")
            return {"result": {"orderId": order_id}, "success": True}
        
        endpoint = "/v5/order/cancel"
        data = {
            "category": self.trading_type,
            "symbol": symbol,
            "orderId": order_id
        }
        
        print(f"REAL_CANCEL: Order {order_id} on Bybit V5 Mainnet - Executing cancel")
        return self._make_request("POST", endpoint, data=data)
    
    def get_open_orders(self, symbol: str = None) -> dict:
        """Get open orders"""
        endpoint = "/v5/order/realtime"
        params = {"category": self.trading_type}
        if symbol:
            params["symbol"] = symbol
        
        if self.paper:
            return {"result": {"list": []}, "success": True}
        
        return self._make_request("GET", endpoint, params)
    
    def get_positions(self, symbol: str = None) -> dict:
        """Get current positions"""
        endpoint = "/v5/position/list"
        params = {"category": self.trading_type}
        if symbol:
            params["symbol"] = symbol
        
        if self.paper:
            return {"result": {"list": []}, "success": True}
        
        return self._make_request("GET", endpoint, params)
    
    def set_leverage(self, symbol: str, leverage: int) -> dict:
        """Set leverage for futures trading"""
        if self.trading_type not in ["linear", "inverse"]:
            return {"error": "Leverage only available for futures trading", "success": False}
        
        if self.paper:
            print(f"PAPER_LEVERAGE: Set {leverage}x leverage for {symbol} on Bybit V5 Testnet")
            return {"result": {"leverage": str(leverage)}, "success": True}
        
        endpoint = "/v5/position/set-leverage"
        data = {
            "category": self.trading_type,
            "symbol": symbol,
            "buyLeverage": str(leverage),
            "sellLeverage": str(leverage)
        }
        
        print(f"REAL_LEVERAGE: Set {leverage}x leverage for {symbol} on Bybit V5 Mainnet")
        return self._make_request("POST", endpoint, data=data)
    
    def set_margin_mode(self, symbol: str, margin_mode: str) -> dict:
        """Set margin mode for futures trading"""
        if self.trading_type not in ["linear", "inverse"]:
            return {"error": "Margin mode only available for futures trading", "success": False}
        
        if self.paper:
            print(f"PAPER_MARGIN: Set {margin_mode} margin for {symbol} on Bybit V5 Testnet")
            return {"result": {"marginMode": margin_mode}, "success": True}
        
        endpoint = "/v5/position/set-margin-mode"
        data = {
            "category": self.trading_type,
            "symbol": symbol,
            "marginMode": margin_mode
        }
        
        print(f"REAL_MARGIN: Set {margin_mode} margin for {symbol} on Bybit V5 Mainnet")
        return self._make_request("POST", endpoint, data=data)
    
    def get_server_time(self) -> dict:
        """Get server time"""
        endpoint = "/v5/market/time"
        return self._make_request("GET", endpoint)
    
    def get_exchange_info(self) -> dict:
        """Get exchange information"""
        endpoint = "/v5/market/instruments-info"
        params = {"category": self.trading_type}
        return self._make_request("GET", endpoint, params)
    
    def get_trading_history(self, symbol: str = None, limit: int = 100) -> dict:
        """Get trading history/executions"""
        endpoint = "/v5/execution/list"
        params = {
            "category": self.trading_type,
            "limit": str(limit)
        }
        if symbol:
            params["symbol"] = symbol
        
        if self.paper:
            return {"result": {"list": []}, "success": True}
        
        return self._make_request("GET", endpoint, params)
    
    def get_order_history(self, symbol: str = None, limit: int = 100) -> dict:
        """Get order history"""
        endpoint = "/v5/order/history"
        params = {
            "category": self.trading_type,
            "limit": str(limit)
        }
        if symbol:
            params["symbol"] = symbol
        
        if self.paper:
            return {"result": {"list": []}, "success": True}
        
        return self._make_request("GET", endpoint, params)
    
    def close(self):
        """Close the executor"""
        pass
