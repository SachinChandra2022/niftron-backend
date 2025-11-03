import os
import psycopg2
from dotenv import load_dotenv


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

SQL_FILE_PATH = os.path.join(PROJECT_ROOT, 'db', 'init', '01-init.sql')

ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

load_dotenv(dotenv_path=ENV_PATH)

def initialize_database():
    """Connects to the database and executes the initialization SQL script."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set in .env file.")

    print("Connecting to the database...")
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        print(f"Reading SQL initialization script from: {SQL_FILE_PATH}")
        with open(SQL_FILE_PATH, "r") as f:
            sql_script = f.read()

        print("Executing SQL script to create tables...")
        cur.execute(sql_script)
        conn.commit()
        print("Database tables created successfully!")

        cur.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    initialize_database()