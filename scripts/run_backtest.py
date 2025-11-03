# scripts/run_backtest.py (COMPLETE VERSION)

import sys
import os
import pandas as pd
import joblib
import scipy.stats as stats
from dotenv import load_dotenv

# --- Pathing ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
load_dotenv(os.path.join(project_root, '.env'))

# --- Imports ---
from niftron.ml_model.data_prep import load_and_prepare_data
from niftron.ml_model.predict import generate_lem_score
# Import our new performance metrics calculator
from niftron.analysis.performance import calculate_performance_metrics

def calculate_she_score(signals_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates the Simple Heuristic Ensemble score."""
    weights = {'trend': 0.4, 'momentum': 0.3, 'macd': 0.3}
    norm_trend = (signals_df['trend_signal'] + 1) * 50
    score = (norm_trend * weights['trend'] + signals_df['momentum_score'] * weights['momentum'] + signals_df['macd_score'] * weights['macd'])
    return pd.DataFrame({'she_score': score}, index=signals_df.index)

def run_simulation_loop(oos_data: pd.DataFrame, score_column: str, portfolio_size: int = 5, rebalance_period: int = 1) -> pd.Series:
    """
    Simulates a daily rebalancing strategy.
    """
    daily_returns = {}
    unique_dates = sorted(oos_data.index.get_level_values('date').unique())

    for date in unique_dates:
        # We make a new decision every day (rebalance_period = 1)
        day_data = oos_data.loc[date]
        
        if not isinstance(day_data, pd.DataFrame) or len(day_data) < portfolio_size:
            daily_returns[date] = 0
            continue
            
        top_stocks = day_data.nlargest(portfolio_size, score_column)
        
        # The portfolio's return for today is the average of the 'daily_return' of the stocks we chose
        day_return = top_stocks['daily_return'].mean()
        daily_returns[date] = day_return

    return pd.Series(daily_returns).fillna(0)

def run_backtest():
    """
    Main function to run the backtesting simulation and print results for all strategies.
    """
    print("--- Starting Backtest Simulation ---")

    # --- Setup and Data Loading ---
    model_path = os.path.join(project_root, 'niftron', 'ml_model', 'lem_model.joblib')
    try:
        lem_model = joblib.load(model_path)
        print("LEM model loaded successfully.")
    except FileNotFoundError:
        print(f"FATAL ERROR: Model file not found at {model_path}. Run training script.")
        return

    full_dataset = load_and_prepare_data()
    test_period_start = pd.to_datetime('2023-01-01')
    oos_data = full_dataset[full_dataset.index >= test_period_start].copy()
    print(f"Backtesting on data from {oos_data.index.min().date()} to {oos_data.index.max().date()}")

    # --- Score Generation ---
    print("\nGenerating scores for all models...")
    she_scores = calculate_she_score(oos_data)
    lem_scores = generate_lem_score(lem_model, oos_data)
    # We already have the base signals in oos_data: 'trend_signal', 'momentum_score', 'macd_score'
    oos_data = pd.concat([oos_data, she_scores, lem_scores], axis=1)
    print("Scores generated.")

    # --- Run Simulations for ALL Strategies ---
    print("\nRunning simulations...")
    # Ensembled Strategies
    she_daily_returns = run_simulation_loop(oos_data, 'she_score')
    lem_daily_returns = run_simulation_loop(oos_data, 'lem_score')
    
    # Base Strategies
    trend_daily_returns = run_simulation_loop(oos_data, 'trend_signal')
    momentum_daily_returns = run_simulation_loop(oos_data, 'momentum_score')
    macd_daily_returns = run_simulation_loop(oos_data, 'macd_score')
    
    # Benchmark
    benchmark_daily_returns = oos_data.groupby('date')['daily_return'].mean().fillna(0)
    print("Simulations complete.")

    # --- Display Performance Results ---
    print("\n--- PERFORMANCE RESULTS ---")
    
    strategies = {
        "Learned Ensemble (LEM)": lem_daily_returns,
        "Simple Heuristic (SHE)": she_daily_returns,
        "Trend-Following Only": trend_daily_returns,
        "Momentum (RSI) Only": momentum_daily_returns,
        "MACD Crossover Only": macd_daily_returns,
        "Benchmark (Equal-Weight)": benchmark_daily_returns
    }

    results_df = []
    for name, returns in strategies.items():
        print(f"\n--- {name} ---")
        metrics = calculate_performance_metrics(returns, benchmark_daily_returns)
        if name == "Benchmark (Equal-Weight)":
            metrics['Alpha (vs. Benchmark)'] = 0.0
            metrics['Beta (vs. Benchmark)'] = 1.0
        
        for metric, value in metrics.items():
            print(f"{metric:<28}: {value:.2f}")
        
        metrics['Strategy'] = name
        results_df.append(metrics)

    print("\n--- Summary Table ---")
    summary = pd.DataFrame(results_df).set_index('Strategy')
    print(summary[['CAGR (%)', 'Sharpe Ratio', 'Max Drawdown (%)']].round(2))
    # Perform a two-sample t-test to see if the difference in returns
    # between LEM and SHE is statistically significant.
    
    # Null Hypothesis (H0): The true mean daily return of LEM is equal to the mean daily return of SHE.
    # Alternative Hypothesis (Ha): The true means are not equal.
    
    t_stat, p_value = stats.ttest_ind(
        lem_daily_returns,
        she_daily_returns,
        equal_var=False # Use Welch's t-test, which doesn't assume equal variance
    )

    print("\n--- Statistical Significance (LEM vs. SHE) ---")
    print(f"T-statistic: {t_stat:.4f}")
    print(f"P-value: {p_value:.4f}")
    
    alpha = 0.05 # Standard significance level
    if p_value < alpha:
        print(f"Result: The p-value is less than {alpha}, so we reject the null hypothesis.")
        print("Conclusion: The difference in performance between LEM and SHE is statistically significant.")
    else:
        print(f"Result: The p-value is greater than {alpha}, so we fail to reject the null hypothesis.")
        print("Conclusion: The difference in performance is not statistically significant.")
        
    print("\n--- Backtest Simulation Finished ---")

if __name__ == '__main__':
    run_backtest()