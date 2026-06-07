from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'tanma',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

with DAG(
    dag_id='etl_weather_pipeline',
    description='ETL pipeline: CSV to clean to Parquet to BigQuery',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'weather', 'bigquery'],
) as dag:

    def run_extract():
        import sys
        sys.path.insert(0, '/opt/airflow/dags')
        from extract import extract
        df = extract('/opt/airflow/dags/weatherAUS.csv')
        if df is None:
            raise ValueError("Extract failed — no data returned")

    extract_task = PythonOperator(
        task_id='extract',
        python_callable=run_extract,
    )

    def run_transform():
        import sys
        sys.path.insert(0, '/opt/airflow/dags')
        from extract import extract
        from transform import clean, fix_schema, save_parquet
        df = extract('/opt/airflow/dags/weatherAUS.csv')
        df = clean(df)
        df = fix_schema(df)
        save_parquet(df, '/opt/airflow/dags/data/processed/weatherAUS.parquet')

    transform_task = PythonOperator(
        task_id='transform',
        python_callable=run_transform,
    )

    def run_load():
        import sys
        sys.path.insert(0, '/opt/airflow/dags')
        from load import load_to_bigquery
        load_to_bigquery(
            parquet_path='/opt/airflow/dags/data/processed/weatherAUS.parquet',
            project_id='etl-weather-pipeline-498619',
            dataset_id='weather_data',
            table_id='daily_weather'
        )

    load_task = PythonOperator(
        task_id='load',
        python_callable=run_load,
    )

    extract_task >> transform_task >> load_task
