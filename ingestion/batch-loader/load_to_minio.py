from minio import Minio
import os
import sys
import argparse
from datetime import datetime

# ---------- MinIO connection ----------
client = Minio(
    "minio:9000",
    access_key="minio_admin",
    secret_key="minio_pass123",
    secure=False
)

BUCKET_NAME = "raw-data"
OUTPUT_DIR = "data-generator/output"

def upload_file(local_path, remote_path):
    if not os.path.exists(local_path):
        print(f"SKIPPED (file not found): {local_path}")
        return False
    client.fput_object(BUCKET_NAME, remote_path, local_path)
    print(f"Uploaded {local_path} -> s3://{BUCKET_NAME}/{remote_path}")
    return True

def load_reference_data():
    upload_file(f"{OUTPUT_DIR}/customers.csv", "reference/customers.csv")
    upload_file(f"{OUTPUT_DIR}/products.csv", "reference/products.csv")

def load_daily_data(target_date):
    orders_file = f"{OUTPUT_DIR}/orders_{target_date}.csv"
    inventory_file = f"{OUTPUT_DIR}/inventory_{target_date}.csv"

    orders_ok = upload_file(orders_file, f"orders/{target_date}/orders_{target_date}.csv")
    inventory_ok = upload_file(inventory_file, f"inventory/{target_date}/inventory_{target_date}.csv")

    if not (orders_ok and inventory_ok):
        print(f"\nWarning: some files for {target_date} were missing. "
              f"Did you run generate_daily_batch.py for this date?")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load generated CSVs into MinIO raw zone.")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.today().strftime("%Y-%m-%d"),
        help="Target date in YYYY-MM-DD format (defaults to today)."
    )
    parser.add_argument(
        "--reference-only",
        action="store_true",
        help="Only load customers/products, skip daily orders/inventory."
    )
    args = parser.parse_args()

    load_reference_data()

    if not args.reference_only:
        load_daily_data(args.date)

    print("\nBatch load to MinIO complete.")