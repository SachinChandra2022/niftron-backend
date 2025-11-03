# src/niftron/processing/main.py

import pandas as pd
import traceback
# We will use executemany, not execute_batch
from psycopg2.extras import execute_values

from niftron.core.db import get_db_connection

def get_stocks_to_process():
    """Fetches all stock IDs from the database."""
    print("Fetching stock list for feature calculation...")
    query = "SELECT stock_id, symbol FROM stocks;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            stocks = cur.fetchall()
    print(f"Found {len(stocks)} stocks to process.")
    return stocks

def calculate_indicators(df):
    """Calculates SMA, RSI, and MACD using pandas."""
    df['SMA_50'] = df['close_price'].rolling(window=50).mean()
    df['SMA_200'] = df['close_price'].rolling(window=200).mean()

    delta = df['close_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    exp12 = df['close_price'].ewm(span=12, adjust=False).mean()
    exp26 = df['close_price'].ewm(span=26, adjust=False).mean()
    df['MACD_12_26_9'] = exp12 - exp26
    df['MACDs_12_26_9'] = df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()
    
    return df

def calculate_and_store_features():
    """
    Calculates technical indicators for each stock and stores them in the 'features' table.
    """
    stocks = get_stocks_to_process()
    
    with get_db_connection() as conn:
        for stock_id, symbol in stocks:
            try:
                print(f"--- Processing features for {symbol} (ID: {stock_id}) ---")

                query = """
                    SELECT date, close_price
                    FROM daily_price_data
                    WHERE stock_id = %s
                    ORDER BY date ASC;
                """
                df = pd.read_sql(query, conn, params=(stock_id,), index_col='date')
                
                if df.empty or len(df) < 200:
                    print(f"Not enough data for {symbol} (found {len(df)} rows). Skipping.")
                    continue

                df = calculate_indicators(df)
                df.dropna(inplace=True)

                if df.empty:
                    print(f"Could not calculate features for {symbol}. Skipping.")
                    continue

                print(f"Calculated {len(df)} rows of features for {symbol}.")
                
                insert_data = []
                for index_date, row in df.iterrows():
                    # --- THE FIX IS HERE ---
                    # Convert all NumPy numeric types to standard Python floats
                    insert_data.append((
                        stock_id,
                        index_date,
                        float(row['SMA_50']),
                        float(row['SMA_200']),
                        float(row['RSI_14']),
                        float(row['MACD_12_26_9']),
                        float(row['MACDs_12_26_9'])
                    ))
                    # --- END OF FIX ---

                if insert_data:
                    insert_query = """
                        INSERT INTO features (
                            stock_id, date, sma_50, sma_200, rsi_14,
                            macd_value, macd_signal
                        ) VALUES %s
                        ON CONFLICT (stock_id, date) DO UPDATE SET
                            sma_50 = EXCLUDED.sma_50,
                            sma_200 = EXCLUDED.sma_200,
                            rsi_14 = EXCLUDED.rsi_14,
                            macd_value = EXCLUDED.macd_value,
                            macd_signal = EXCLUDED.macd_signal;
                    """
                    with conn.cursor() as cur:
                        # Use execute_values for efficient bulk insert/update
                        execute_values(cur, insert_query, insert_data)
                    conn.commit()
                    print(f"Successfully stored {len(insert_data)} feature records for {symbol}.")
            
            except Exception:
                print(f"!!! An error occurred while processing features for {symbol} !!!")
                traceback.print_exc()
                conn.rollback()

    print("\n--- Feature engineering complete! ---")

def run():
    """Entry point for Airflow to trigger the feature engineering process."""
    print("Starting Niftron Feature Engineering...")
    calculate_and_store_features()
    print("Niftron Feature Engineering Finished.")

if __name__ == "__main__":
    run()