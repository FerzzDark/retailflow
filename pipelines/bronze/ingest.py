"""
Bronze layer: raw ingestion of M5 CSVs into BigQuery.

Uploads raw files to GCS and loads them into BigQuery without transformation,
preserving the original data for reproducibility and auditing.
"""
import os
from pathlib import Path
from google.cloud import bigquery, storage

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "retailflow")
DATASET = "bronze"
BUCKET = os.getenv("GCS_BUCKET", "retailflow-data")

RAW_FILES = {
    "bronze_sales": "sales_train_validation.csv",
    "bronze_calendar": "calendar.csv",
    "bronze_prices": "sell_prices.csv",
}


def upload_to_gcs(local_path: str, blob_name: str) -> str:
    """Upload a local file to Google Cloud Storage."""
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET)
    blob = bucket.blob(f"bronze/{blob_name}")
    blob.upload_from_filename(local_path)
    uri = f"gs://{BUCKET}/bronze/{blob_name}"
    print(f"Uploaded {local_path} -> {uri}")
    return uri


def load_to_bigquery(table_name: str, gcs_uri: str) -> None:
    """Load a CSV from GCS into a BigQuery table (autodetect schema)."""
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )
    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()
    table = client.get_table(table_id)
    print(f"Loaded {table.num_rows} rows into {table_id}")


def run(data_dir: str = "data/raw") -> None:
    """Run the full bronze ingestion pipeline."""
    for table_name, filename in RAW_FILES.items():
        local_path = Path(data_dir) / filename
        if not local_path.exists():
            print(f"WARNING: {local_path} not found, skipping")
            continue
        gcs_uri = upload_to_gcs(str(local_path), filename)
        load_to_bigquery(table_name, gcs_uri)


if __name__ == "__main__":
    run()
