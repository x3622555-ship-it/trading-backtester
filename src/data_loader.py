# src/data_loader.py
import csv
from datetime import datetime
from typing import List
from pathlib import Path

from models import MarketDataPoint


def load_market_data(csv_path: str) -> List[MarketDataPoint]:
    """
    Load CSV into a sorted list of MarketDataPoint.
    Expected CSV header: timestamp,symbol,price
    timestamp should be ISO format or "%Y-%m-%d %H:%M:%S"
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"{csv_path} not found")

    rows = []
    with path.open(newline='') as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            ts_raw = row.get("timestamp") or row.get("time") or row.get("date")
            if ts_raw is None:
                raise ValueError(f"Missing timestamp on row {i+1}")
            # try ISO first, fallback to common format
            try:
                ts = datetime.fromisoformat(ts_raw)
            except Exception:
                ts = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
            symbol = row.get("symbol") or row.get("ticker") or "UNKNOWN"
            price = float(row.get("price") or row.get("close") or 0)
            rows.append(MarketDataPoint(timestamp=ts, symbol=symbol.strip(), price=float(price)))

    # sort by timestamp to ensure chronological order
    rows.sort(key=lambda r: r.timestamp)
    return rows
