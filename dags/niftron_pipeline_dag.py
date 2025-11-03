from __future__ import annotations
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pendulum
from airflow.decorators import dag, task

from niftron.ingestion import main as ingestion_main
from niftron.processing import main as processing_main
from niftron.analysis import main as analysis_main


@dag(
    dag_id="niftron_daily_pipeline",
    schedule_interval="0 18 * * 1-5",  
    start_date=pendulum.datetime(2024, 5, 20, tz="UTC"),
    catchup=False,
    tags=["niftron", "production"],
    doc_md="""
    ### Niftron Daily Pipeline
    This DAG orchestrates the daily workflow for the Niftron project:
    1. **Ingest** – Fetches the latest daily stock data.  
    2. **Process** – Calculates technical indicators (features).  
    3. **Analyze** – Runs algorithms, ensembles scores, and stores top 5 recommendations.
    """
)
def niftron_daily_pipeline():
    """Defines the Niftron ETL + analysis workflow."""

    @task()
    def ingest_data():
        """Run the data ingestion script."""
        ingestion_main.run()

    @task()
    def process_features():
        """Run the feature engineering script."""
        processing_main.run()

    @task()
    def analyze_and_rank():
        """Run the analysis and ranking script."""
        analysis_main.run()

    # Define the execution flow
    ingest_task = ingest_data()
    process_task = process_features()
    analyze_task = analyze_and_rank()

    ingest_task >> process_task >> analyze_task

dag = niftron_daily_pipeline()