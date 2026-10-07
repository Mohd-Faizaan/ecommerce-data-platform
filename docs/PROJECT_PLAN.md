# E-Commerce Data Platform — Project Plan

## 1. What This Project Is

An end-to-end data engineering platform that simulates a real e-commerce company's
data infrastructure — handling both **batch** data (orders, customers, inventory)
and **streaming** data (clickstream events), from raw ingestion all the way to
business dashboards.

This mirrors what companies like Amazon, Flipkart, or Swiggy build internally.

---

## 2. Architecture — The 5 Zones

Data moves through five distinct zones, never skipping one:

```
[Simulated Sources]
   → Kafka (streaming) / Files (batch)              [Zone 1: Ingestion]
   → MinIO raw storage, Bronze layer                 [Zone 2: Raw Lake]
   → Spark + dbt clean & model → Silver → Gold        [Zone 3: Batch Transform]
   → Spark Streaming computes live metrics            [Zone 3: Stream Transform]
   → Great Expectations validates before load          [Zone 4: Quality Gate]
   → Postgres/Snowflake (Gold) + Postgres/Redis (live) [Zone 5: Serving]
   → Metabase/Superset dashboards                      [Consumption]
```

**Airflow** sits above all of this as the orchestrator — it triggers and
sequences every batch step, retries failures, and alerts on problems.
**Status: working** — the DAG currently runs `generate_daily_data >>
load_to_minio >> clean_with_spark` fully automatically, daily, with zero
manual steps. The Spark task is triggered via `docker exec` into the
`spark-master` container (Docker socket mounted into Airflow) — see
Progress doc for how this was wired up.

### Zone 0 — Data Origin (sources being simulated)
- Transactional data (batch): orders, customers, products, inventory
- Clickstream data (streaming): page views, searches, cart actions
- Inventory updates (semi-batch): daily stock snapshots

### Zone 1 — Ingestion Layer
- Kafka producer pushes clickstream + order events in real time
- Batch loader drops daily CSV/JSON files (simulating nightly exports)

### Zone 2 — Raw Storage / Data Lake (Bronze layer)
- Everything lands in MinIO (local S3) untouched, partitioned by date
- Kept raw for reprocessing and auditability

### Zone 3 — Processing & Transformation
- **Batch:** ✅ Spark cleans raw data → Silver layer (done, automated in
  Airflow). dbt builds Gold layer star schema (`fact_orders`,
  `dim_customers`, `dim_products`, `dim_date`), including SCD Type 2 for
  product price history — not started yet
- **Streaming:** Spark Structured Streaming computes live windowed metrics
  (orders/minute, top products right now) from Kafka directly — not
  started yet

### Zone 4 — Data Quality Gate
- Great Expectations validates data before it's allowed to load
  (no nulls in keys, no negative amounts, valid foreign keys, sane row counts)

### Zone 5 — Serving Layer
- Warehouse (Postgres) holds the Gold star schema → daily BI dashboards
- Fast-access store holds live metrics → real-time operational dashboard

---

## 3. Tech Stack

| Component | Tool | Why |
|---|---|---|
| Ingestion (streaming) | Kafka + Zookeeper | Industry-standard event streaming |
| Ingestion (batch) | Python + Airflow | Simulates scheduled file exports |
| Storage (data lake) | MinIO | Free, local, S3-compatible |
| Orchestration | Apache Airflow | Schedules, retries, monitors pipelines (custom image extending the base, with project dependencies + scripts mounted in) |
| Processing | Apache Spark (official `apache/spark` image, master + worker) | Batch + streaming transformation at scale |
| Modeling | dbt | Star schema, tests, SCD Type 2 |
| Data quality | Great Expectations | Automated validation gate |
| Warehouse | PostgreSQL | Final business-ready tables |
| Dashboards | Metabase / Superset | BI layer for consumption |
| Infra | Docker Compose | Everything runs locally, free, reproducible |

**Resource profile:** Full stack (6-core CPU, 16GB RAM, Windows + WSL2)

---

## 4. Build Order (Phases)

1. ✅ **Environment setup** — Docker, Python venv, Git/GitHub, folder skeleton
2. ✅ **Core infra** — docker-compose.yml bringing up Postgres (x2), MinIO,
   Kafka/Zookeeper, Airflow (webserver + scheduler)
3. ✅ **Data generators** — fake customers/products (one-time), daily
   orders/inventory (batch), clickstream events (streaming via Kafka)
4. ✅ **Ingestion wiring** — land raw generator output into MinIO (Bronze)
5. ✅ **Orchestration** — Airflow DAGs to schedule batch ingestion
6. ✅ **Spark cleaning** — Bronze → Silver, wired into Airflow, fully
   automated daily run (dbt star schema / SCD Type 2 for Gold layer still
   pending — see item 6b below)
6b. ⬜ **dbt modeling** — Silver → Gold star schema + SCD Type 2 — **next up**
7. ⬜ **Streaming layer** — Spark Structured Streaming on Kafka topics for
   live metrics
8. ⬜ **Data quality gate** — Great Expectations checks wired into Airflow
9. ⬜ **Serving + dashboards** — Metabase/Superset connected to warehouse
10. ⬜ **Polish** — architecture diagram, README, design-decision notes

---

## 5. Repo Structure

```
ecommerce-data-platform/
├── docker-compose.yml
├── .env
├── data-generator/        # customer/product/order/inventory generators
├── ingestion/
│   ├── kafka-producer/    # clickstream producer
│   └── batch-loader/      # lands batch files into MinIO
├── airflow/
│   ├── dags/                # includes ecommerce_batch_pipeline.py (working DAG)
│   ├── plugins/
│   ├── Dockerfile          # extends base Airflow image: project deps +
│   │                       # docker-ce-cli (to control spark-master via
│   │                       # the mounted host Docker socket)
│   └── requirements.txt    # faker, pandas, minio, kafka-python
├── spark-jobs/
│   ├── batch/               # includes clean_orders_inventory.py (working)
│   └── streaming/
├── dbt-project/
├── great-expectations/
├── dashboards/
└── docs/
```
