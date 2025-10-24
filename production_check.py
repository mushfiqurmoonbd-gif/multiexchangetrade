#!/usr/bin/env python3
"""
Production Environment Checker
Validates that all required settings are configured for production trading
"""

import os
import sys
from dotenv import load_dotenv

def check_production_ready():
    """Check if environment is ready for production trading"""
    load_dotenv()
    
    print("PRODUCTION READINESS CHECK")
    print("=" * 50)
    
    # Check API keys
    exchanges = ['BINANCE', 'BYBIT', 'MEXC']
    api_keys_configured = 0
    
    for exchange in exchanges:
        api_key = os.getenv(f"{exchange}_API_KEY")
        api_secret = os.getenv(f"{exchange}_API_SECRET")
        
        if api_key and api_secret:
            print(f"[OK] {exchange}: API keys configured")
            api_keys_configured += 1
        else:
            print(f"[ERROR] {exchange}: API keys missing")
    
    print(f"\nAPI Keys Status: {api_keys_configured}/{len(exchanges)} exchanges configured")
    
    # Production warnings
    print("\nPRODUCTION WARNINGS:")
    print("• This will place REAL orders with REAL money")
    print("• Ensure sufficient account balance")
    print("• Test strategies thoroughly before live trading")
    print("• Monitor positions closely")
    print("• Use proper risk management settings")
    
    # Final check
    if api_keys_configured > 0:
        print(f"\nPRODUCTION READY: {api_keys_configured} exchange(s) configured")
        print("Proceed with caution - Real trading enabled!")
        return True
    else:
        print("\nNOT PRODUCTION READY: No API keys configured")
        print("Configure API keys in .env file before running production")
        return False

if __name__ == "__main__":
    check_production_ready()
