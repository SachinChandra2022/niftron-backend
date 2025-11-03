# src/niftron/analysis/strategies/trend_strategy.py

import pandas as pd

def generate_signals(features_df):
    """
    Generates trading signals based on SMA crossovers (Golden/Death Cross).
    
    Args:
        features_df (pd.DataFrame): DataFrame with features, indexed by date.
                                    Must contain 'sma_50' and 'sma_200' columns.

    Returns:
        pd.DataFrame: The input DataFrame with a new 'trend_signal' column.
                      Signal values: 1 (Golden Cross), -1 (Death Cross), 0 (Neutral).
    """
    df = features_df.copy()

    # A Golden Cross occurs when the 50-day SMA crosses ABOVE the 200-day SMA.
    # A Death Cross occurs when the 50-day SMA crosses BELOW the 200-day SMA.

    # Condition 1: Is the 50-day SMA currently above the 200-day SMA?
    condition_currently_bullish = df['sma_50'] > df['sma_200']
    
    # Condition 2: Was it below in the previous period?
    # We use .shift(1) to look at the previous day's data.
    condition_previously_bearish = df['sma_50'].shift(1) < df['sma_200'].shift(1)
    
    # A Golden Cross is when both conditions are true.
    df['golden_cross'] = condition_currently_bullish & condition_previously_bearish

    # For the Death Cross, the logic is reversed.
    condition_currently_bearish = df['sma_50'] < df['sma_200']
    condition_previously_bullish = df['sma_50'].shift(1) > df['sma_200'].shift(1)
    df['death_cross'] = condition_currently_bearish & condition_previously_bullish

    # Assign scores based on the crosses
    df['trend_signal'] = 0
    df.loc[df['golden_cross'], 'trend_signal'] = 1
    df.loc[df['death_cross'], 'trend_signal'] = -1

    # We only need the final signal column
    return df[['trend_signal']]