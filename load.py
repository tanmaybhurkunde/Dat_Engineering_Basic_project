import pandas as pd
import logging
import pyarrow as pa
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError 
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler("pipeline.log", mode='a')
file_handler.setLevel(logging.DEBUG)

# Shared format for both
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

def load_to_bigquery(parquet_path, project_id, dataset_id, table_id):
    logger.info(f"Starting load to BigQuery...")
    logger.info(f"Parameters: project={project_id}, dataset={dataset_id}, table={table_id}")

    # Task A: read parquet file
    try:
        # Check if parquet file exists
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
        
        # Read the parquet file
        df = pd.read_parquet(parquet_path)
        logger.info(f"Successfully read parquet file: {parquet_path}")
        logger.info(f"DataFrame shape: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Log memory usage and data types
        memory_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        logger.info(f"DataFrame memory usage: {memory_usage_mb:.2f} MB")
        
    except Exception as e:
        logger.error(f"Failed to read parquet file: {e}")
        raise



    # Task B: create client and load to BigQuery
    try:
            # Initialize BigQuery client
            client = bigquery.Client(project=project_id)
            logger.info(f"BigQuery client created for project: {project_id}")
            
            # Set up table reference
            table_ref = f"{project_id}.{dataset_id}.{table_id}"
            logger.info(f"Target table: {table_ref}")
            
            # Configure load job
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Overwrite table if exists
                create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,  # Create table if doesn't exist
                autodetect=True,  # Auto-detect schema
            )
            
            # Load data to BigQuery
            logger.info(f"Starting load job for {len(df)} rows...")
            load_job = client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            
            # Wait for job to complete
            load_job.result()  # Blocks until complete
            
            # Check job status
            if load_job.errors:
                logger.error(f"Load job had errors: {load_job.errors}")
                raise Exception(f"Load job failed: {load_job.errors}")
            
            logger.info(f"Load job completed successfully. Job ID: {load_job.job_id}")
            
    except GoogleAPIError as e:
        logger.error(f"Google API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load data to BigQuery: {e}")
        raise


    # Task C: verify by querying row count
    try:
        # Query to count rows in the newly loaded table
        query = f"""
            SELECT COUNT(*) as row_count
            FROM `{project_id}.{dataset_id}.{table_id}`
        """
        
        logger.info("Verifying data in BigQuery...")
        query_job = client.query(query)
        results = query_job.result()
        
        for row in results:
            bq_row_count = row.row_count
        
        logger.info(f"Row count verification:")
        logger.info(f"  - Parquet file: {len(df)} rows")
        logger.info(f"  - BigQuery table: {bq_row_count} rows")
        
        if len(df) == bq_row_count:
            logger.info(" Row count verification PASSED!")
        else:
            logger.warning(f" Row count mismatch: Parquet has {len(df)}, BigQuery has {bq_row_count}")
        
    except Exception as e:
        logger.error(f"Failed to verify data in BigQuery: {e}")
        logger.warning("Data was loaded but verification query failed")

    # Task D: log completion

    logger.info("=" * 60)
    logger.info("BIGQUERY LOAD SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Source file: {parquet_path}")
    logger.info(f"Target table: {table_ref}")
    logger.info(f"Rows loaded: {len(df):,}")
    logger.info(f"Columns loaded: {len(df.columns)}")
    logger.info(f"Project: {project_id}")
    logger.info(f"Dataset: {dataset_id}")
    logger.info("=" * 60)
    logger.info("Load to BigQuery complete!")
    
    return True

if __name__ == "__main__":
    load_to_bigquery(
        parquet_path = "data/weather_cleaned.parquet",
        project_id   = "etl-weather-pipeline-498619",
        dataset_id   = "weather_data",
        table_id     = "daily_weather"
    )