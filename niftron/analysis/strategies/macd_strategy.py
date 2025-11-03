# src/niftron/analysis/strategies/macd_strategy.py

import pandas as pd

def generate_signals(features_df):
    """
    Generates a signal based on the MACD crossover.

    Args:
        features_df (pd.DataFrame): DataFrame with features, indexed by date.
                                    Must contain 'macd_value' and 'macd_signal'.

    Returns:
        pd.DataFrame: A DataFrame with a 'macd_signal_strength' column.
                      Score is 100 for a bullish cross, 0 for a bearish cross.
    """
    df = features_df.copy()

    # Rename columns for clarity
    df.rename(columns={'macd_value': 'macd', 'macd_signal': 'macds'}, inplace=True)

    # Bullish signal: MACD crosses ABOVE its signal line.
    condition_currently_bullish = df['macd'] > df['macds']
    condition_previously_bearish = df['macd'].shift(1) < df['macds'].shift(1)
    df['bullish_cross'] = condition_currently_bullish & condition_previously_bearish

    # Bearish signal: MACD crosses BELOW its signal line.
    condition_currently_bearish = df['macd'] < df['macds']
    condition_previously_bullish = df['macd'].shift(1) > df['macds'].shift(1)
    df['bearish_cross'] = condition_currently_bearish & condition_previously_bullish
    
    # We'll create a simple score: 100 for a fresh bullish signal, 0 otherwise.
    # More advanced logic could provide scores for "sustained" bullishness.
    df['macd_score'] = 0
    df.loc[df['bullish_cross'], 'macd_score'] = 100
    # We could assign a negative score for bearish, but for a "buy" recommender,
    # we are mainly interested in positive signals.

    return df[['macd_score']]