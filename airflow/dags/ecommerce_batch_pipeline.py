from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "mohd-faizaan",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

SPARK_PACKAGES = "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262"

with DAG(
    dag_id="ecommerce_batch_pipeline",
    default_args=default_args,
    description="Generates daily orders/inventory, loads to MinIO, cleans with Spark",
    schedule_interval="@daily",
    start_date=datetime(2026, 10, 1),
    catchup=False,
    tags=["ecommerce", "batch", "ingestion", "spark"],
) as dag:

    generate_daily_data = BashOperator(
        task_id="generate_daily_data",
        bash_command="cd /opt/airflow/project && python data-generator/generate_daily_batch.py --date {{ ds }}",
    )

    load_to_minio = BashOperator(
        task_id="load_to_minio",
        bash_command="cd /opt/airflow/project && python ingestion/batch-loader/load_to_minio.py --date {{ ds }}",
    )

    clean_with_spark = BashOperator(
        task_id="clean_with_spark",
        bash_command=(
            "docker exec spark-master /opt/spark/bin/spark-submit "
            f"--packages {SPARK_PACKAGES} "
            "/opt/spark-jobs/batch/clean_orders_inventory.py {{ ds }}"
        ),
    )

    generate_daily_data >> load_to_minio >> clean_with_spark