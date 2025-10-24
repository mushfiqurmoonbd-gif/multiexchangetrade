import os
import csv
from datetime import datetime


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def log_trade(file_path: str, record: dict):
    _ensure_dir(file_path)
    exists = os.path.exists(file_path)
    # Add mode and timestamp
    record['log_timestamp'] = datetime.utcnow().isoformat()
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(record.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(record)
    
    # Mode-specific console logging with exchange info
    exchange = record.get('exchange', 'Unknown')
    if record.get('status') == 'paper':
        print(f"PAPER_TRADE_LOGGED on {exchange}: {record}")
    else:
        print(f"REAL_TRADE_LOGGED on {exchange}: {record}")


def log_pnl(file_path: str, equity: float):
    _ensure_dir(file_path)
    exists = os.path.exists(file_path)
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ts','equity'])
        if not exists:
            writer.writeheader()
        writer.writerow({'ts': datetime.utcnow().isoformat(), 'equity': float(equity)})


