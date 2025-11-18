import pandas as pd
import joblib
import os
from cachetools import cached, TTLCache
from niftron.ml_model.data_prep import load_and_prepare_data
from niftron.ml_model.predict import generate_lem_score
from niftron.analysis.performance import calculate_performance_metrics
simulation_cache = TTLCache(maxsize=1, ttl=43200)
cache = TTLCache(maxsize=1, ttl=43200)



def calculate_she_score(signals_df: pd.DataFrame) -> pd.DataFrame:
    weights = {'trend': 0.4, 'momentum': 0.3, 'macd': 0.3}
    norm_trend = (signals_df['trend_signal'] + 1) * 50
    score = (norm_trend * weights['trend'] + signals_df['momentum_score'] * weights['momentum'] + signals_df['macd_score'] * weights['macd'])
    return pd.DataFrame({'she_score': score}, index=signals_df.index)

def run_simulation_loop(oos_data: pd.DataFrame, score_column: str, portfolio_size: int = 5) -> pd.Series:
    daily_returns = {}
    unique_dates = sorted(oos_data.index.get_level_values('date').unique())

    for date in unique_dates:
        day_data = oos_data.loc[date]
        if not isinstance(day_data, pd.DataFrame) or len(day_data) < portfolio_size:
            daily_returns[date] = 0
            continue
        top_stocks = day_data.nlargest(portfolio_size, score_column)
        day_return = top_stocks['daily_return'].mean()
        daily_returns[date] = day_return
    return pd.Series(daily_returns).fillna(0)


# --- MAIN FUNCTION FOR API (NOW CACHED) ---

# --- ADD THIS DECORATOR ---
@cached(simulation_cache)
def run_all_simulations():
    """
    Runs all simulations and returns the raw daily returns for each strategy.
    This is the core expensive function that is now cached.
    """
    print("--- SIMULATION CACHE MISS: Running all backtest simulations... ---")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    model_path = os.path.join(project_root, 'niftron', 'ml_model', 'lem_model.joblib')
    
    lem_model = joblib.load(model_path)
    full_dataset = load_and_prepare_data()
    test_period_start = pd.to_datetime('2023-01-01')
    oos_data = full_dataset[full_dataset.index >= test_period_start].copy()

    she_scores = calculate_she_score(oos_data)
    lem_scores = generate_lem_score(lem_model, oos_data)
    oos_data = pd.concat([oos_data, she_scores, lem_scores], axis=1)

    lem_returns = run_simulation_loop(oos_data, 'lem_score')
    she_returns = run_simulation_loop(oos_data, 'she_score')
    benchmark_returns = oos_data.groupby('date')['daily_return'].mean().fillna(0)
    
    return lem_returns, she_returns, benchmark_returns

# --- UPDATED FUNCTION FOR PERFORMANCE ENDPOINT ---
def get_backtest_results() -> dict:
    """
    Calculates performance metrics based on the cached simulation results.
    """
    lem_returns, she_returns, benchmark_returns = run_all_simulations()

    lem_metrics = calculate_performance_metrics(lem_returns, benchmark_returns)
    she_metrics = calculate_performance_metrics(she_returns, benchmark_returns)
    benchmark_metrics = calculate_performance_metrics(benchmark_returns, benchmark_returns)
    
    return { "lem": lem_metrics, "she": she_metrics, "benchmark": benchmark_metrics }
