# src/reporting.py
import pandas as pd
import numpy as np

def calculate_total_return(df: pd.DataFrame) -> float:
    """
    Calculates total return percentage based on the first and last price.
    """
    if df.empty or 'price' not in df.columns:
        return 0.0
    start_price = df['price'].iloc[0]
    end_price = df['price'].iloc[-1]
    total_return = ((end_price - start_price) / start_price) * 100
    return float(round(total_return, 2))

def calculate_sharpe_ratio(df: pd.DataFrame, risk_free_rate: float = 0.0) -> float:
    """
    Calculates the Sharpe ratio given price data.
    """
    if df.empty or 'price' not in df.columns:
        return 0.0
    df['returns'] = df['price'].pct_change().dropna()
    excess_returns = df['returns'] - (risk_free_rate / 252)
    std_dev = excess_returns.std()
    mean_excess = excess_returns.mean()
    if std_dev == 0 or np.isnan(std_dev):
        return 0.0
    sharpe = (mean_excess / std_dev) * np.sqrt(252)
    return float(round(sharpe, 2))
