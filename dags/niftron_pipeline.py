# dags/niftron_pipeline.py
from __future__ import annotations
import pendulum
from airflow.decorators import dag, task

# With PYTHONPATH=/opt/airflow set in docker-compose, this should work directly.
from niftron.ingestion import main as ingestion_main
from niftron.processing import main as processing_main
from niftron.analysis import main as analysis_main

@dag(
    dag_id="niftron_daily_pipeline",
    schedule="0 18 * * 1-5",
    start_date=pendulum.datetime(2024, 5, 20, tz="UTC"),
    catchup=False,
    tags=["niftron", "production"],
    doc_md="""
    ### Niftron Daily Pipeline
    This DAG orchestrates the daily workflow for the Niftron project.
    """
)
def niftron_daily_pipeline():
    @task()
    def ingest_data():
        ingestion_main.run()

    @task()
    def process_features():
        processing_main.run()

    @task()
    def analyze_and_rank():
        analysis_main.run()

    ingest_data() >> process_features() >> analyze_and_rank()

niftron_daily_pipeline()