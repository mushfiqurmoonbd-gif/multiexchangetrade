import os
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv
from pybit.unified_trading import HTTP  # correct import for latest pybit

# Load environment variables from .env
load_dotenv()

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")
BYBIT_IS_TESTNET = os.getenv("BYBIT_IS_TESTNET", "True") == "True"

MEXC_API_KEY = os.getenv("MEXC_API_KEY")
MEXC_API_SECRET = os.getenv("MEXC_API_SECRET")

# -------- BYBIT SETUP --------
BYBIT_ENDPOINT = "https://api-testnet.bybit.com" if BYBIT_IS_TESTNET else "https://api.bybit.com"

bybit_client = HTTP(
    endpoint=BYBIT_ENDPOINT,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

def check_bybit():
    try:
        resp = bybit_client.get_wallet_balance(account_type="UNIFIED")
        print("Bybit Response:", resp)
        return resp
    except Exception as e:
        print("Bybit Error:", e)
        return {"error": str(e)}

# -------- MEXC CHECK --------
def check_mexc():
    if not MEXC_API_KEY or not MEXC_API_SECRET:
        return {"error": "MEXC API key/secret missing!"}

    url = "https://api.mexc.com/api/v3/account"
    timestamp = str(int(time.time() * 1000))
    query = f"timestamp={timestamp}"
    signature = hmac.new(MEXC_API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    headers = {"X-MEXC-APIKEY": MEXC_API_KEY}

    try:
        resp = requests.get(f"{url}?{query}&signature={signature}", headers=headers, timeout=10)
        print("MEXC Status:", resp.status_code)
        print("MEXC Response:", resp.json())
        return resp.json()
    except Exception as e:
        print("MEXC Error:", e)
        return {"error": str(e)}

if __name__ == "__main__":
    print("🔍 Checking Bybit API...")
    check_bybit()

    print("\n🔍 Checking MEXC API...")
    check_mexc()
