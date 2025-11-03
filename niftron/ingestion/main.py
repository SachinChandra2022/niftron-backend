# src/niftron/ingestion/main.py

import yfinance as yf
import pandas as pd
import traceback
from psycopg2.extras import execute_batch

from niftron.core.db import get_db_connection
from niftron.core.config import settings

def get_stocks_from_db():
    # ... (This function is unchanged)
    print("Fetching stock list from database...")
    query = "SELECT stock_id, symbol FROM stocks;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            stocks = cur.fetchall()
    print(f"Found {len(stocks)} stocks to process.")
    return stocks

def populate_price_data():
    # ... (This function has the final fix)
    stocks_to_process = get_stocks_from_db()
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for stock_id, symbol in stocks_to_process:
                try:
                    ticker = f"{symbol}{settings.MARKET_SUFFIX}"
                    print(f"--- Processing {ticker} ---")

                    data = yf.download(ticker, period="5y", interval="1d", auto_adjust=False, progress=False)

                    if data.empty:
                        print(f"No data found for {ticker}. Skipping.")
                        continue
                    
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    
                    print(f"Fetched {len(data)} rows for {ticker}. Columns flattened.")

                    data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'], inplace=True)
                    data = data[data['Volume'] > 0]

                    print(f"Cleaned data, {len(data)} rows remaining.")

                    insert_data = []
                    for index, row in data.iterrows():
                        trade_date = index.date()
                        
                        # --- THE FINAL FIX ---
                        # Explicitly convert NumPy types to standard Python types.
                        # float() and int() will handle np.float64 and np.int64 correctly.
                        insert_data.append((
                            stock_id, 
                            trade_date,
                            float(row['Open']),
                            float(row['High']),
                            float(row['Low']),
                            float(row['Close']),
                            float(row['Adj Close']),
                            int(row['Volume'])
                        ))
                        # --- END OF FIX ---
                    
                    if insert_data:
                        insert_query = """
                            INSERT INTO daily_price_data (
                                stock_id, date, open_price, high_price, low_price, 
                                close_price, adjusted_close_price, volume
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (stock_id, date) DO NOTHING;
                        """
                        # We will switch back to executemany as it's more robust with parameter substitution
                        cur.executemany(insert_query, insert_data)
                        conn.commit()
                        print(f"Successfully processed and stored {len(insert_data)} records for {ticker}.")

                except Exception:
                    print(f"!!! An unexpected error occurred while processing {symbol} !!!")
                    traceback.print_exc()
                    conn.rollback()
    
    print("\n--- Data ingestion complete! ---")

def run():
    """Entry point for Airflow to trigger the ingestion process."""
    print("Starting Niftron Data Ingestion...")
    populate_price_data()
    print("Niftron Data Ingestion Finished.")

if __name__ == "__main__":
    run()