import pandas as pd
from sqlalchemy import create_engine
from minio import Minio
import io

client = Minio(
    "localhost:9000",
    access_key="minio_admin",
    secret_key="minio_pass123",
    secure=False
)

engine = create_engine("postgresql+psycopg2://warehouse_user:warehouse_pass123@localhost:5434/ecommerce_warehouse")

def load_reference_table(object_name, table_name):
    response = client.get_object("raw-data", f"reference/{object_name}")
    df = pd.read_csv(io.BytesIO(response.read()))
    df.to_sql(table_name, engine, schema="staging", if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into staging.{table_name}")

if __name__ == "__main__":
    load_reference_table("customers.csv", "customers")
    load_reference_table("products.csv", "products")