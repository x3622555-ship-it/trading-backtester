# src/main.py
import argparse
import json
from pathlib import Path

from .data_loader import load_market_data
from .strategies import MovingAverageCrossover
from .engine import Engine
from .reporting import total_return, sharpe_ratio, max_drawdown


def main():
    parser = argparse.ArgumentParser(description="Simple CSV-based backtester")
    parser.add_argument("--csv", required=True, help="Path to market data CSV")
    parser.add_argument("--symbol", required=False, default=None, help="Symbol to trade (optional)")
    parser.add_argument("--out", required=False, default="results.json", help="Output summary JSON")
    args = parser.parse_args()

    market_data = load_market_data(args.csv)
    if not market_data:
        print("No market data loaded.")
        return

    # if symbol is not provided, pick the first symbol in the data
    symbol = args.symbol or market_data[0].symbol

    # instantiate a strategy
    strat = MovingAverageCrossover(symbol=symbol, short_window=3, long_window=7)

    # engine with deterministic RNG and small simulated failure rate of 0.01 (1%)
    engine = Engine(strategies=[strat], initial_cash=100000.0, rng_seed=1, execution_failure_rate=0.01)
    engine.run(market_data)

    # compute metrics
    tr = total_return(engine.equity_curve, engine.initial_cash)
    sr = sharpe_ratio(engine.equity_curve)
    mdd = max_drawdown(engine.equity_curve)

    summary = engine.summary()
    summary.update({
        "total_return": tr,
        "sharpe_ratio": sr,
        "max_drawdown": mdd
    })

    out_path = Path(args.out)
    out_path.write_text(json.dumps(summary, default=str, indent=2))
    print(f"Backtest finished. Summary written to {out_path}")


if __name__ == "__main__":
    main()
