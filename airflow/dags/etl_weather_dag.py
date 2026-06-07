from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Default arguments applied to every task
default_args = {
    'owner': 'tanma',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

# DAG definition
with DAG(
    dag_id='etl_weather_pipeline',
    description='ETL pipeline: CSV → clean → Parquet → BigQuery',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'weather', 'bigquery'],
) as dag:

    # Task 1 — Extract
    def run_extract():
        import sys
        sys.path.insert(0, '/opt/airflow/dags')
        from extract import extract
        df = extract('/opt/airflow/dags/weatherAUS.csv')  # ← full path
        if df is None:
            raise ValueError("Extract failed — no data returned")

    extract_task = PythonOperator(
        task_id='extract',
        python_callable=run_extract,
    )

    # Task 2 — Transform
    def run_transform():
        import sys
        sys.path.insert(0, '/opt/airflow/dags')
        from extract import extract
        from transform import clean, fix_schema, save_parquet
        df = extract('/opt/airflow/dags/weatherAUS.csv')  # ← full path
        df = clean(df)
        df = fix_schema(df)
        save_parquet(df, '/opt/airflow/dags/data/processed/weatherAUS.parquet')  # ← full path
    transform_task = PythonOperator(
        task_id='transform',
        python_callable=run_transform,
    )

    # Task 3 — Load
    def run_load():
        import sys
        sys.path.insert(0, '/opt/airflow/dags')
        from load import load_to_bigquery
        load_to_bigquery(
            parquet_path='/opt/airflow/dags/data/processed/weatherAUS.parquet',  # ← full path
            project_id='etl-weather-pipeline-498619',
            dataset_id='weather_data',
            table_id='daily_weather'
        )

    load_task = PythonOperator(
        task_id='load',
        python_callable=run_load,
    )

    # Set task dependencies — extract → transform → load
    extract_task >> transform_task >> load_task