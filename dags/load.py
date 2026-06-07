import pandas as pd
import logging
from google.cloud import bigquery
import os

def load_to_bigquery(parquet_path, project_id, dataset_id, table_id):
    logger = logging.getLogger(__name__)
    logger.info("Starting load to BigQuery...")
    logger.info(f"Parameters: project={project_id}, dataset={dataset_id}, table={table_id}")

    df = pd.read_parquet(parquet_path)
    logger.info(f"Read {df.shape[0]} rows, {df.shape[1]} columns from parquet")

    client = bigquery.Client(project=project_id)
    destination = f"{project_id}.{dataset_id}.{table_id}"
    logger.info(f"Target table: {destination}")

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, destination, job_config=job_config)
    job.result()
    logger.info(f"Load job completed. Job ID: {job.job_id}")

    query = f"SELECT COUNT(*) as row_count FROM `{destination}`"
    for row in client.query(query).result():
        logger.info(f"BigQuery row count: {row.row_count}")
        if row.row_count == df.shape[0]:
            logger.info("Row count verification PASSED!")
        else:
            logger.warning(f"Mismatch! Parquet: {df.shape[0]}, BigQuery: {row.row_count}")

    logger.info("Load to BigQuery complete!")

if __name__ == "__main__":
    load_to_bigquery(
        parquet_path="data/processed/weatherAUS.parquet",
        project_id="etl-weather-pipeline-498619",
        dataset_id="weather_data",
        table_id="daily_weather"
    )
