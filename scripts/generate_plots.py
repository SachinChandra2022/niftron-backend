# scripts/generate_plots.py

import sys
import os
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import json

# Add project root to path to allow imports from the 'niftron' package
project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root_path)

from niftron.ml_model.data_prep import load_and_prepare_data
from niftron.ml_model.predict import generate_lem_score
from scripts.sync_frontend_assets import sync_assets

# --- Simulation Helper Functions ---

def calculate_she_score(signals_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates the Simple Heuristic Ensemble score."""
    weights = {'trend': 0.4, 'momentum': 0.3, 'macd': 0.3}
    norm_trend = (signals_df['trend_signal'] + 1) * 50
    score = (norm_trend * weights['trend'] + signals_df['momentum_score'] * weights['momentum'] + signals_df['macd_score'] * weights['macd'])
    return pd.DataFrame({'she_score': score}, index=signals_df.index)

def run_simulation_loop(oos_data: pd.DataFrame, score_column: str, portfolio_size: int = 5) -> pd.Series:
    """Simulates a daily rebalancing strategy."""
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

# --- Plotting and Data Generation Functions ---

def save_chart_data_to_json(returns_df: pd.DataFrame, filename: str):
    """Saves the daily returns data to a JSON file for the frontend."""
    print(f"Saving chart data to: {filename}")
    chart_data = {
        'dates': returns_df.index.strftime('%Y-%m-%d').tolist(),
        'lem_returns': returns_df['Learned Ensemble (LEM)'].tolist(),
        'she_returns': returns_df['Simple Heuristic (SHE)'].tolist(),
        'benchmark_returns': returns_df['NIFTY 50 Benchmark'].tolist()
    }
    with open(filename, 'w') as f:
        json.dump(chart_data, f, indent=2)
    print("Chart data saved.")

def plot_equity_curve(returns_df: pd.DataFrame, filename: str):
    """Calculates and plots the cumulative returns (equity curve)."""
    print(f"Generating Equity Curve plot: {filename}")
    cumulative_returns = (1 + returns_df).cumprod()
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    cumulative_returns.plot(ax=ax)
    ax.set_title('Growth of a Hypothetical $1 Investment (Equity Curve)', fontsize=16)
    ax.set_ylabel('Cumulative Returns')
    ax.set_xlabel('Date')
    ax.legend(title='Strategy')
    fig.tight_layout()
    plt.savefig(filename)
    plt.close()
    print("Plot saved.")

def plot_drawdown_curves(returns_df: pd.DataFrame, filename: str):
    """Calculates and plots the drawdown for each strategy."""
    print(f"Generating Drawdown Curves plot: {filename}")
    cumulative_returns = (1 + returns_df).cumprod()
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns / peak) - 1
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    (drawdown * 100).plot(ax=ax)
    ax.set_title('Strategy Drawdown from Peak Equity', fontsize=16)
    ax.set_ylabel('Drawdown (%)')
    ax.set_xlabel('Date')
    ax.legend(title='Strategy')
    fig.tight_layout()
    plt.savefig(filename)
    plt.close()
    print("Plot saved.")

def plot_feature_importance(model, feature_names: list, filename: str):
    """Plots the feature importances of the trained model."""
    print(f"Generating Feature Importance plot: {filename}")
    importances = model.feature_importances_
    model_feature_names = model.feature_names_in_
    importance_map = dict(zip(model_feature_names, importances))
    
    internal_names = ['trend_signal', 'momentum_score', 'macd_score']
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': [importance_map.get(name, 0) for name in internal_names]
    }).sort_values(by='Importance', ascending=False)
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df, ax=ax, palette='viridis')
    ax.set_title('Relative Feature Importance for LEM', fontsize=16)
    ax.set_xlabel('Importance Score')
    ax.set_ylabel('Feature (Base Signal)')
    fig.tight_layout()
    plt.savefig(filename)
    plt.close()
    print("Plot saved.")
    
# --- Main Execution ---

def main():
    """Main function to generate all plots, data, and sync to frontend."""
    print("--- Starting Asset Generation & Sync ---")

    output_dir = os.path.join(project_root_path, 'paper_figures')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generated assets will be temporarily saved in: {output_dir}")

    # 1. Load Model
    model_path = os.path.join(project_root_path, 'niftron', 'ml_model', 'lem_model.joblib')
    try:
        lem_model = joblib.load(model_path)
    except FileNotFoundError:
        print(f"ERROR: Model file not found at {model_path}. Please run the training script first.")
        return

    # 2. Load and Prepare Data
    full_dataset = load_and_prepare_data()
    test_period_start = pd.to_datetime('2023-01-01')
    oos_data = full_dataset[full_dataset.index >= test_period_start].copy()

    # 3. Generate Scores and Run Simulations
    she_scores = calculate_she_score(oos_data)
    lem_scores = generate_lem_score(lem_model, oos_data)
    oos_data = pd.concat([oos_data, she_scores, lem_scores], axis=1)

    lem_returns = run_simulation_loop(oos_data, 'lem_score')
    she_returns = run_simulation_loop(oos_data, 'she_score')
    benchmark_returns = oos_data.groupby('date')['daily_return'].mean().fillna(0)
    
    returns_df = pd.DataFrame({
        'Learned Ensemble (LEM)': lem_returns,
        'Simple Heuristic (SHE)': she_returns,
        'NIFTY 50 Benchmark': benchmark_returns
    })
    
    # 4. Generate and Save All Artifacts
    save_chart_data_to_json(returns_df, os.path.join(output_dir, 'chart-data.json'))
    plot_equity_curve(returns_df, os.path.join(output_dir, 'equity_curve.png'))
    plot_drawdown_curves(returns_df, os.path.join(output_dir, 'drawdown_plot.png'))
    plot_feature_importance(
        lem_model, 
        ['Trend Signal', 'Momentum (RSI)', 'MACD Signal'], 
        os.path.join(output_dir, 'feature_importance.png')
    )
    
    print("\n--- Asset generation complete ---")

    # 5. Automatically sync the generated assets to the frontend
    sync_assets()
    
    print("\n--- All artifacts generated and synced successfully! ---")

if __name__ == '__main__':
    main()