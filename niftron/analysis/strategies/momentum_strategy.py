# src/niftron/analysis/strategies/momentum_strategy.py

import pandas as pd
import numpy as np

def generate_signals(features_df):
    """
    Generates a momentum score based on the RSI.
    The score is normalized to be between 0 and 100, where higher is more bullish.

    Args:
        features_df (pd.DataFrame): DataFrame with features, indexed by date.
                                    Must contain an 'rsi_14' column.

    Returns:
        pd.DataFrame: The input DataFrame with a new 'momentum_score' column.
    """
    df = features_df.copy()
    
    # RSI Scoring Logic:
    # - RSI < 30 is typically considered oversold (strong buy signal).
    # - RSI > 70 is typically considered overbought (strong sell signal).
    # We want a score where 100 is the most bullish.
    # So, we can simply invert the RSI scale.
    # A low RSI (e.g., 20) should result in a high score (e.g., 80).
    # A high RSI (e.g., 80) should result in a low score (e.g., 20).
    
    # Simple inversion: score = 100 - RSI
    df['momentum_score'] = 100 - df['rsi_14']

    return df[['momentum_score']]