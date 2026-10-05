from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, upper, to_date
import sys

def get_spark_session():
    return (
        SparkSession.builder
        .appName("CleanOrdersInventory")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minio_admin")
        .config("spark.hadoop.fs.s3a.secret.key", "minio_pass123")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate()
    )

def clean_orders(spark, target_date):
    raw_path = f"s3a://raw-data/orders/{target_date}/orders_{target_date}.csv"
    df = spark.read.option("header", True).option("inferSchema", True).csv(raw_path)

    cleaned = (
        df.dropDuplicates(["order_id"])
          .dropna(subset=["order_id", "customer_id", "product_id"])
          .withColumn("order_status", trim(upper(col("order_status"))))
          .withColumn("order_date", to_date(col("order_date"), "yyyy-MM-dd"))
          .filter(col("total_amount") > 0)
    )

    silver_path = f"s3a://raw-data/silver/orders/{target_date}/"
    cleaned.write.mode("overwrite").parquet(silver_path)

    print(f"Cleaned orders: {df.count()} raw -> {cleaned.count()} after cleaning")
    print(f"Written to {silver_path}")

def clean_inventory(spark, target_date):
    raw_path = f"s3a://raw-data/inventory/{target_date}/inventory_{target_date}.csv"
    df = spark.read.option("header", True).option("inferSchema", True).csv(raw_path)

    cleaned = (
        df.dropDuplicates(["product_id", "snapshot_date"])
          .dropna(subset=["product_id"])
          .filter(col("stock_quantity") >= 0)
    )

    silver_path = f"s3a://raw-data/silver/inventory/{target_date}/"
    cleaned.write.mode("overwrite").parquet(silver_path)

    print(f"Cleaned inventory: {df.count()} raw -> {cleaned.count()} after cleaning")
    print(f"Written to {silver_path}")

if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    if not target_date:
        print("Usage: clean_orders_inventory.py <YYYY-MM-DD>")
        sys.exit(1)

    spark = get_spark_session()
    clean_orders(spark, target_date)
    clean_inventory(spark, target_date)
    spark.stop()