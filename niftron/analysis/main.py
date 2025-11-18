# src/niftron/analysis/main.py

import pandas as pd
import traceback
import json
import joblib
import os

from niftron.core.db import get_db_connection
from niftron.analysis.strategies import trend_strategy, momentum_strategy, macd_strategy

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
model_path = os.path.join(project_root, 'niftron', 'ml_model', 'lem_model.joblib')
try:
    lem_model = joblib.load(model_path)
    print("LEM model loaded successfully for analysis.")
except FileNotFoundError:
    lem_model = None
    print("WARNING: lem_model.joblib not found. LEM scores will not be calculated.")

STRATEGY_WEIGHTS = {
    'trend': 0.40,
    'momentum': 0.30,
    'macd': 0.30
}

def get_all_features():
    """Fetches all features for all stocks from the database."""
    print("Fetching all features from the database...")
    query = """
        SELECT 
            s.stock_id, 
            s.symbol,
            f.date,
            f.sma_50,
            f.sma_200,
            f.rsi_14,
            f.macd_value,
            f.macd_signal
        FROM features f
        JOIN stocks s ON s.stock_id = f.stock_id
        ORDER BY s.symbol, f.date ASC;
    """
    # --- END OF FIX ---

    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)
    print(f"Successfully fetched {len(df)} total feature records.")
    return df

def run_analysis_and_rank():
    """
    Runs all analysis, calculates scores for BOTH models, ensembles the results,
    ranks stocks for each model, and stores the top 5 of each.
    """
    all_features_df = get_all_features()
    if all_features_df.empty:
        print("No features found. Run processing module first.")
        return

    grouped = all_features_df.groupby('symbol')
    latest_results = []

    print("\nRunning analysis strategies for each stock...")
    for symbol, features_df in grouped:
        try:
            df = features_df.set_index('date').sort_index()
            if df.empty:
                continue

            # --- Generate Base Signals ---
            trend_signals = trend_strategy.generate_signals(df)
            momentum_signals = momentum_strategy.generate_signals(df)
            macd_signals = macd_strategy.generate_signals(df)
            
            combined = pd.concat([trend_signals, momentum_signals, macd_signals], axis=1)
            if combined.empty:
                continue
                
            last_day = combined.iloc[-1]
            
            # --- Calculate SHE Score (Heuristic) ---
            she_weights = {'trend': 0.40, 'momentum': 0.30, 'macd': 0.30}
            norm_trend = (last_day['trend_signal'] + 1) * 50
            she_score = (norm_trend * she_weights['trend'] + 
                         last_day['momentum_score'] * she_weights['momentum'] + 
                         last_day['macd_score'] * she_weights['macd'])
            
            # --- Calculate LEM Score (Machine Learning) ---
            lem_score = 0
            if lem_model:
                features_for_lem = pd.DataFrame({
                    'trend_signal': [last_day['trend_signal']],
                    'momentum_score': [last_day['momentum_score']],
                    'macd_score': [last_day['macd_score']]
                })
                # predict_proba gives [prob_of_0, prob_of_1], we want the latter
                lem_probability = lem_model.predict_proba(features_for_lem)[0][1]
                lem_score = lem_probability * 100 # Scale to 0-100

            latest_results.append({
                'stock_id': features_df['stock_id'].iloc[0],
                'symbol': symbol,
                'date': last_day.name,
                'she_score': she_score,
                'lem_score': lem_score,
                'raw_scores': {
                    'trend_signal': last_day['trend_signal'],
                    'momentum_score': last_day['momentum_score'],
                    'macd_score': last_day['macd_score']
                }
            })
        except Exception:
            print(f"--- Error processing {symbol} ---")
            traceback.print_exc()

    if not latest_results:
        print("Could not generate any results.")
        return

    results_df = pd.DataFrame(latest_results)

    # --- Rank and select Top 5 for EACH model ---
    top_5_she = results_df.sort_values(by='she_score', ascending=False).head(5)
    top_5_lem = results_df.sort_values(by='lem_score', ascending=False).head(5)

    recommendations_to_store = []
    
    # Prepare SHE recommendations
    rank_counter = 1
    for _, row in top_5_she.iterrows():
        recommendations_to_store.append({
            'date': row['date'],
            'rank': rank_counter,
            'stock_id': row['stock_id'],
            'score': row['she_score'],
            'model_type': 'SHE',
            'algorithm_scores': row['raw_scores']
        })
        rank_counter += 1
        
    # Prepare LEM recommendations
    rank_counter = 1 # Reset the counter for the second model
    for _, row in top_5_lem.iterrows():
        recommendations_to_store.append({
            'date': row['date'],
            'rank': rank_counter,
            'stock_id': row['stock_id'],
            'score': row['lem_score'],
            'model_type': 'LEM',
            'algorithm_scores': row['raw_scores']
        })
        rank_counter += 1

    store_recommendations(pd.DataFrame(recommendations_to_store))


def store_recommendations(reco_df):
    """Saves the top recommendations for both models to the database."""
    print("\nStoring top 5 recommendations for SHE and LEM models...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Clear previous recommendations for the same day
            delete_query = "DELETE FROM recommendations WHERE date = %s;"
            cur.execute(delete_query, (reco_df['date'].iloc[0],))

            # Insert new recommendations
            insert_query = """
                INSERT INTO recommendations (date, rank, stock_id, score, model_type, algorithm_scores)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            insert_data = [
                (row['date'], row['rank'], int(row['stock_id']), float(row['score']), row['model_type'], json.dumps(row['algorithm_scores']))
                for _, row in reco_df.iterrows()
            ]
            cur.executemany(insert_query, insert_data)
        conn.commit()
    print("Successfully stored recommendations.")

def run():
    """Entry point for Airflow to trigger the analysis and ranking process."""
    print("Starting Niftron Analysis and Ranking...")
    run_analysis_and_rank()
    print("Niftron Analysis and Ranking Finished.")

if __name__ == "__main__":
    run()