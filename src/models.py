# src/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MarketDataPoint:
    """Immutable record for a single market tick."""
    timestamp: datetime
    symbol: str
    price: float


class OrderError(Exception):
    """Raised for invalid orders (bad quantity, price, etc.)."""
    pass


class ExecutionError(Exception):
    """Raised when an order fails execution."""
    pass


class Order:
    """
    Simple order object.
    `side` is "BUY" or "SELL".
    `quantity` is positive integer (number of units).
    `price` is the limit price for execution (float).
    """
    def __init__(self, symbol: str, side: str, quantity: int, price: float):
        if side not in ("BUY", "SELL"):
            raise OrderError("side must be 'BUY' or 'SELL'")
        if quantity <= 0:
            raise OrderError("quantity must be > 0")
        if price <= 0:
            raise OrderError("price must be > 0")

        self.symbol = symbol
        self.side = side
        self.quantity = int(quantity)
        self.price = float(price)
        self.status = "NEW"          # NEW, FILLED, FAILED
        self.filled_quantity = 0
        self.fill_price: Optional[float] = None

    def __repr__(self):
        return (f"Order({self.side} {self.quantity} {self.symbol} @ {self.price:.2f} "
                f"status={self.status})")