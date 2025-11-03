# src/niftron/ml_model/data_prep.py

import pandas as pd
from niftron.core.db import get_db_connection
from niftron.analysis.strategies import trend_strategy, momentum_strategy, macd_strategy

def _generate_signals_for_stock(df: pd.DataFrame) -> pd.DataFrame:
    """Applies all base strategy signal calculations to a single stock's feature dataframe."""
    trend_signals = trend_strategy.generate_signals(df)
    momentum_signals = momentum_strategy.generate_signals(df)
    macd_signals = macd_strategy.generate_signals(df)
    
    # The signal names match the paper's feature names
    combined = pd.concat([trend_signals, momentum_signals, macd_signals], axis=1)
    combined.rename(columns={
        'trend_signal': 'trend_signal',
        'momentum_score': 'momentum_score',
        'macd_score': 'macd_score'
    }, inplace=True)
    return combined

# In src/niftron/ml_model/data_prep.py in the generate_target_variable function

def generate_target_variable(df: pd.DataFrame, horizon: int = 10, threshold: float = 0.02) -> pd.DataFrame:
    df = df.copy()
    
    # 10-day forward return for the target
    future_price_10d = df['close_price'].shift(-horizon)
    df['future_return'] = (future_price_10d / df['close_price']) - 1
    
    # Target label
    df['target'] = (df['future_return'] > threshold).astype(int)

    # --- ADD THIS ---
    # 1-day forward return for backtesting simulation
    future_price_1d = df['close_price'].shift(-1)
    df['daily_return'] = (future_price_1d / df['close_price']) - 1
    # --- END ADD ---

    return df

def load_and_prepare_data() -> pd.DataFrame:
    """
    Loads all features and price data from the database, merges them,
    generates signals and the target variable for each stock.
    
    Returns:
        pd.DataFrame: A single, cleaned DataFrame ready for model training.
    """
    print("Loading all features and price data from the database...")
    query = """
    SELECT
        s.symbol,
        f.date,
        f.sma_50,
        f.sma_200,
        f.rsi_14,
        f.macd_value,
        f.macd_signal,
        p.close_price
    FROM features f
    JOIN stocks s ON s.stock_id = f.stock_id
    JOIN daily_price_data p ON p.stock_id = f.stock_id AND p.date = f.date
    ORDER BY s.symbol, f.date ASC;
    """
    with get_db_connection() as conn:
        full_df = pd.read_sql(query, conn, index_col='date', parse_dates=['date'])

    print(f"Loaded {len(full_df)} total records.")
    
    all_stocks_data = []
    # Group by stock symbol and apply calculations independently
    for symbol, group in full_df.groupby('symbol'):
        print(f"Processing data for {symbol}...")
        
        # 1. Generate the base signals (our features for the LEM)
        signals_df = _generate_signals_for_stock(group)
        
        # 2. Generate the target variable using close prices
        target_df = generate_target_variable(group[['close_price']])
        
        # 3. Combine signals and target
        combined_group = pd.concat([signals_df, target_df], axis=1)
        combined_group['symbol'] = symbol
        
        all_stocks_data.append(combined_group)
        
    # Combine all processed stock data back into one DataFrame
    final_df = pd.concat(all_stocks_data)
    
    # Drop rows with NaN values, which occur at the start/end of the series
    # due to rolling windows and future-looking target.
    final_df.dropna(inplace=True)
    
    print(f"Data preparation complete. Final dataset has {len(final_df)} rows.")
    
    return final_df