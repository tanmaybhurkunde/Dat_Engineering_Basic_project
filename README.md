# 🌦️ ETL Weather Pipeline

An end-to-end data engineering pipeline that extracts Australian weather data from a raw CSV file, cleans and enriches it using Python and Pandas, converts it to Parquet format, loads it into Google BigQuery, and orchestrates the entire flow using Apache Airflow running on Docker.

---

## Architecture

```
weatherAUS.csv (raw, 13.44 MB)
        │
        ▼
┌───────────────┐
│   Extract     │  reads CSV · validates · logs missing data
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Transform   │  drops bad columns · fills nulls · fixes schema
│               │  engineers features · saves as Parquet (2.35 MB)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│     Load      │  uploads to Google BigQuery · verifies row count
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Airflow    │  orchestrates all three tasks · runs @daily
│    (Docker)   │  automatic retry · timestamped logs
└───────────────┘
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| Transformation | Pandas · PyArrow |
| File Format | Parquet (columnar storage) |
| Cloud Warehouse | Google BigQuery |
| Orchestration | Apache Airflow 2.9.1 |
| Containerisation | Docker · Docker Compose |
| Version Control | Git · GitHub |

---

## Project Structure

```
├── extract.py               # Extract stage — reads and validates CSV
├── transform.py             # Transform stage — cleans, enriches, saves Parquet
├── load.py                  # Load stage — uploads Parquet to BigQuery
├── dags/
│   └── etl_weather_dag.py   # Airflow DAG — orchestrates all three stages
├── data/
│   └── weatherAUS.csv       # Raw dataset (145,460 rows, 23 columns)
├── docker-compose.yaml      # Airflow services configuration
├── .gitignore
└── README.md
```

---

## Dataset

**Source:** [Rain in Australia — Kaggle](https://www.kaggle.com/datasets/jsphyg/weather-dataset-rattle-package)

| Property | Value |
|---|---|
| Rows | 145,460 |
| Columns | 23 (raw) → 27 (after feature engineering) |
| Date range | 2008 – 2017 |
| Locations | 49 Australian weather stations |

---

## Pipeline Details

### Extract
- Reads raw CSV with encoding handling and error recovery
- Logs row count, column count, and missing data percentage
- Raises clean errors on missing files — no silent failures

### Transform
- Drops columns with more than 40% missing values (`Evaporation`, `Sunshine`, `Cloud3pm`)
- Fills numeric nulls with column median (outlier-safe)
- Fills categorical nulls with `"Unknown"`
- Converts `Date` column from string to `datetime64`
- Engineers three new features:
  - `temp_range` — daily temperature volatility (max − min)
  - `is_hot_day` — boolean flag for days exceeding 35°C
  - `season` — Australian seasonal classification from month
- Saves cleaned data as Parquet — **82.5% smaller than source CSV**

### Load
- Reads Parquet file and uploads to BigQuery using `WRITE_TRUNCATE`
- Verifies row count matches after every load
- Logs BigQuery Job ID for traceability

### Orchestration
- Airflow DAG with `@daily` schedule and 1 automatic retry per task
- `catchup=False` — no backfill on first run
- Tasks: `extract >> transform >> load`

---

## Results

**File size comparison:**
```
CSV (raw):      13.44 MB
Parquet:         2.35 MB  →  82.5% reduction
```

**Missing data handled:**
```
Total missing values:  343,248  (10.3% of dataset)
Columns dropped:       3        (> 40% missing)
Remaining nulls:       0        (after median/Unknown fill)
```

**BigQuery SQL result — seasonal analysis:**
```sql
SELECT season, ROUND(AVG(maxtemp), 2) AS avg_max_temp,
       ROUND(AVG(rainfall), 2) AS avg_rainfall, COUNT(*) AS total_days
FROM `etl-weather-pipeline-498619.weather_data.daily_weather`
GROUP BY season ORDER BY avg_max_temp DESC;
```

| Season | Avg Max Temp | Avg Rainfall | Total Days |
|--------|-------------|--------------|------------|
| Summer | 28.64°C | 2.73mm | 35,122 |
| Autumn | 23.51°C | 2.33mm | 38,264 |
| Spring | 23.49°C | 1.88mm | 35,337 |
| Winter | 17.47°C | 2.29mm | 36,737 |

---

## Setup & Running

### Prerequisites
- Docker Desktop
- Google Cloud account with BigQuery API enabled
- A GCP Service Account key with BigQuery Admin role

### 1. Clone the repository
```bash
git clone https://github.com/tanmaybhurkunde/Dat_Engineering_Basic_project.git
cd Dat_Engineering_Basic_project
```

### 2. Add your GCP credentials
Place your service account JSON key in the project root as `gcp-key.json`.
This file is gitignored and must never be committed.

### 3. Set environment variables
```bash
echo "AIRFLOW_UID=50000" > .env
```

### 4. Start Airflow
```bash
docker-compose up airflow-init
docker-compose up -d
```

### 5. Open the Airflow UI
Go to `http://localhost:8080` — login with `airflow / airflow`

### 6. Trigger the pipeline
Find `etl_weather_pipeline` → toggle on → click ▶ Trigger DAG

---

## Key Learnings

- Columnar storage (Parquet) reduces file size by 82.5% vs CSV
- Median is safer than mean for filling missing values in skewed data
- Airflow DAGs separate pipeline logic from orchestration concerns
- Docker isolates the Airflow environment from local dependencies
- Google Cloud service accounts are the correct auth pattern for containerised workloads

---

## Author

**Tanmay Bhurkunde**
[GitHub](https://github.com/tanmaybhurkunde) · [LinkedIn](#)
