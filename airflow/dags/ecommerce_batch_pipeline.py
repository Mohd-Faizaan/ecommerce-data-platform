from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "mohd-faizaan",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="ecommerce_batch_pipeline",
    default_args=default_args,
    description="Generates daily orders/inventory and loads them into MinIO raw zone",
    schedule_interval="@daily",
    start_date=datetime(2026, 10, 1),
    catchup=False,
    tags=["ecommerce", "batch", "ingestion"],
) as dag:

    generate_daily_data = BashOperator(
        task_id="generate_daily_data",
        bash_command="cd /opt/airflow/project && python data-generator/generate_daily_batch.py",
    )

    load_to_minio = BashOperator(
        task_id="load_to_minio",
        bash_command="cd /opt/airflow/project && python ingestion/batch-loader/load_to_minio.py --date {{ ds }}",
    )

    generate_daily_data >> load_to_minio