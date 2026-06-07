import pandas as pd
import logging
from google.cloud import bigquery

# your logger setup (same pattern as extract.py and transform.py)

def load_to_bigquery(parquet_path, project_id, dataset_id, table_id):
    
    logger.info(f"Starting load to BigQuery...")

    # Task A: read parquet file

    # Task B: create client and load to BigQuery

    # Task C: verify by querying row count

    # Task D: log completion

if __name__ == "__main__":
    load_to_bigquery(
        parquet_path = "data/weather_cleaned.parquet",
        project_id   = "etl-weather-pipeline-498619",
        dataset_id   = "weather_data",
        table_id     = "daily_weather"
    )