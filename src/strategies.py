# src/strategies.py
from abc import ABC, abstractmethod
from collections import deque
from typing import List, Tuple

from .models import MarketDataPoint

Signal = Tuple[str, str, int, float]
# (ACTION, SYMBOL, QTY, PRICE) where ACTION is "BUY" or "SELL"


class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        """Return a list of signals given a MarketDataPoint."""
        pass


class MovingAverageCrossover(Strategy):
    """
    Simple SMA crossover strategy.
    Emits a BUY when short_ma > long_ma and last action was not buy.
    Emits a SELL when short_ma < long_ma and last action was not sell.
    """
    def __init__(self, symbol: str, short_window: int = 5, long_window: int = 20):
        if short_window >= long_window:
            raise ValueError("short_window must be < long_window")
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self._prices = deque(maxlen=long_window)
        self._last_signal = None  # "BUY" or "SELL" or None

    def generate_signals(self, tick: MarketDataPoint):
        if tick.symbol != self.symbol:
            return []
        self._prices.append(tick.price)
        if len(self._prices) < self.long_window:
            return []

        long_ma = sum(list(self._prices)[-self.long_window:]) / self.long_window
        short_ma = sum(list(self._prices)[-self.short_window:]) / self.short_window

        if short_ma > long_ma and self._last_signal != "BUY":
            self._last_signal = "BUY"
            return [("BUY", self.symbol, 1, tick.price)]
        elif short_ma < long_ma and self._last_signal != "SELL":
            self._last_signal = "SELL"
            return [("SELL", self.symbol, 1, tick.price)]
        return []


class MomentumStrategy(Strategy):
    """
    Simple momentum: compare current price to price N ticks ago.
    If return > threshold -> BUY, if return < -threshold -> SELL
    """
    def __init__(self, symbol: str, lookback: int = 5, threshold: float = 0.01):
        self.symbol = symbol
        self.lookback = lookback
        self.threshold = threshold
        self._prices = deque(maxlen=lookback + 1)

    def generate_signals(self, tick: MarketDataPoint):
        if tick.symbol != self.symbol:
            return []
        self._prices.append(tick.price)
        if len(self._prices) <= self.lookback:
            return []
        current = self._prices[-1]
        prev = self._prices[0]
        ret = (current / prev) - 1.0
        if ret > self.threshold:
            return [("BUY", self.symbol, 1, tick.price)]
        elif ret < -self.threshold:
            return [("SELL", self.symbol, 1, tick.price)]
        return []
