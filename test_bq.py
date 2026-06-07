from google.cloud import bigquery

client = bigquery.Client(project="etl-weather-pipeline-498619")
print(f"Connected to project: {client.project}")

# List datasets to confirm connection
datasets = list(client.list_datasets())
print(f"Datasets found: {[d.dataset_id for d in datasets]}")