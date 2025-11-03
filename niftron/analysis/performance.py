# src/niftron/analysis/performance.py

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

def calculate_performance_metrics(daily_returns: pd.Series, benchmark_daily_returns: pd.Series) -> dict:
    """
    Calculates a comprehensive set of performance metrics for a strategy.

    Args:
        daily_returns (pd.Series): A pandas Series of daily returns for the strategy.
        benchmark_daily_returns (pd.Series): A pandas Series of daily returns for the benchmark.

    Returns:
        dict: A dictionary containing all the calculated performance metrics.
    """
    if daily_returns.empty:
        return {}

    # --- Return Metrics ---
    total_return = (1 + daily_returns).prod() - 1
    cagr = ((1 + total_return) ** (TRADING_DAYS_PER_YEAR / len(daily_returns))) - 1

    # --- Risk Metrics ---
    annualized_volatility = daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    # Calculate Drawdown
    cumulative_returns = (1 + daily_returns).cumprod()
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min()

    # --- Risk-Adjusted Return Metrics ---
    sharpe_ratio = (cagr / annualized_volatility) if annualized_volatility != 0 else 0
    
    # Sortino Ratio (uses downside deviation)
    negative_returns = daily_returns[daily_returns < 0]
    downside_deviation = negative_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    sortino_ratio = (cagr / downside_deviation) if downside_deviation != 0 else 0
    
    calmar_ratio = (cagr / abs(max_drawdown)) if max_drawdown != 0 else 0

    # --- Metrics Relative to Benchmark ---
    # Beta and Alpha calculation
    covariance = daily_returns.cov(benchmark_daily_returns)
    benchmark_variance = benchmark_daily_returns.var()
    beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
    
    # Alpha = Strategy CAGR - Beta * Benchmark CAGR
    benchmark_total_return = (1 + benchmark_daily_returns).prod() - 1
    benchmark_cagr = ((1 + benchmark_total_return) ** (TRADING_DAYS_PER_YEAR / len(benchmark_daily_returns))) - 1
    alpha = cagr - (beta * benchmark_cagr)

    # --- Trading Statistics ---
    win_rate = (daily_returns > 0).sum() / len(daily_returns) if len(daily_returns) > 0 else 0

    return {
        "CAGR (%)": cagr * 100,
        "Annualized Volatility (%)": annualized_volatility * 100,
        "Sharpe Ratio": sharpe_ratio,
        "Sortino Ratio": sortino_ratio,
        "Calmar Ratio": calmar_ratio,
        "Max Drawdown (%)": max_drawdown * 100,
        "Alpha (vs. Benchmark)": alpha * 100,
        "Beta (vs. Benchmark)": beta,
        "Win Rate (%)": win_rate * 100
    }