# src/engine.py
import random
from typing import List, Dict, Tuple
from datetime import datetime

from .models import MarketDataPoint, Order, OrderError, ExecutionError


class Engine:
    """
    Backtest engine that:
    - Accepts strategies (list)
    - Runs through market data ticks
    - Converts signals into Orders and attempts execution
    - Records positions and equity curve
    """

    def __init__(self, strategies: List, initial_cash: float = 100000.0, rng_seed: int = 42, execution_failure_rate: float = 0.0):
        self.strategies = strategies
        self.cash = float(initial_cash)
        self.initial_cash = float(initial_cash)
        self.positions: Dict[str, Dict[str, float]] = {}  # symbol -> {'quantity': int, 'avg_price': float}
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.logs: List[str] = []
        self.execution_failure_rate = float(execution_failure_rate)
        random.seed(rng_seed)

    def _validate_order(self, order: Order):
        if order.quantity <= 0:
            raise OrderError("quantity must be > 0")
        if order.price <= 0:
            raise OrderError("price must be > 0")

    def _execute_order(self, order: Order):
        """
        Simulate execution: may raise ExecutionError if random failure triggers.
        Assumes immediate fill at order.price; BUY reduces cash, SELL increases cash.
        """
        # possible simulated failure
        if random.random() < self.execution_failure_rate:
            raise ExecutionError("simulated execution failure")

        qty = order.quantity if order.side == "BUY" else -order.quantity
        symbol = order.symbol
        price = order.price
        position = self.positions.get(symbol, {"quantity": 0, "avg_price": 0.0})
        # BUY
        if qty > 0:
            total_cost = qty * price
            # update avg price
            existing_qty = position["quantity"]
            if existing_qty == 0:
                position["avg_price"] = price
            else:
                position["avg_price"] = ((existing_qty * position["avg_price"]) + total_cost) / (existing_qty + qty)
            position["quantity"] = existing_qty + qty
            self.cash -= total_cost
            order.status = "FILLED"
            order.filled_quantity = qty
            order.fill_price = price
        else:
            # SELL
            sell_qty = -qty
            existing_qty = position["quantity"]
            if sell_qty > existing_qty:
                # allow short? For simplicity, prevent selling more than we have (raise)
                raise ExecutionError(f"attempt to sell {sell_qty} but only {existing_qty} held")
            position["quantity"] = existing_qty - sell_qty
            # if position reduced to zero, zero avg_price
            if position["quantity"] == 0:
                position["avg_price"] = 0.0
            self.cash += sell_qty * price
            order.status = "FILLED"
            order.filled_quantity = sell_qty
            order.fill_price = price

        self.positions[symbol] = position

    def _market_value(self, current_tick: MarketDataPoint):
        total = self.cash
        for sym, pos in self.positions.items():
            qty = pos["quantity"]
            if qty == 0:
                continue
            if sym == current_tick.symbol:
                price = current_tick.price
            else:
                # fallback to avg_price if no recent price for other symbols
                price = pos["avg_price"]
            total += qty * price
        return total

    def run(self, market_data: List[MarketDataPoint]):
        """
        Main loop: for each tick, get signals from strategies, convert to orders,
        attempt execution, and append equity snapshot.
        """
        for tick in market_data:
            # collect signals
            signals = []
            for strat in self.strategies:
                try:
                    s = strat.generate_signals(tick)
                    if s:
                        signals.extend(s)
                except Exception as e:
                    self.logs.append(f"Strategy error for {strat}: {e}")

            # process signals into orders
            for action, symbol, qty, price in signals:
                try:
                    order = Order(symbol=symbol, side=action, quantity=qty, price=price)
                    self._validate_order(order)
                    try:
                        self._execute_order(order)
                    except ExecutionError as ee:
                        order.status = "FAILED"
                        self.logs.append(f"ExecutionError: {ee} -> {order}")
                except OrderError as oe:
                    self.logs.append(f"OrderError: {oe} -> {(action, symbol, qty, price)}")

            # record equity snapshot
            try:
                equity = self._market_value(tick)
            except Exception:
                equity = self.cash  # fallback
            self.equity_curve.append((tick.timestamp, equity))

    def summary(self):
        return {
            "initial_cash": self.initial_cash,
            "final_cash": self.cash,
            "positions": self.positions,
            "equity_curve_length": len(self.equity_curve),
            "logs": self.logs[:20]
        }
