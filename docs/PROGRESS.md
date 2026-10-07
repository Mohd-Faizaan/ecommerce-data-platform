# Project Progress Tracker

_Last updated: based on work completed through Step 7 (full pipeline automated end-to-end in Airflow, including Spark)_

---

## ✅ Completed

### Environment Setup
- [x] Docker Desktop installed, WSL2 backend enabled (Windows)
- [x] Python 3.12 + virtual environment (`venv`) created and activated
- [x] Git repo initialized and pushed to GitHub (`Mohd-Faizaan/ecommerce-data-platform`)
- [x] Full project folder skeleton created with `.gitkeep` placeholders
- [x] `.gitignore` configured (Python artifacts, `.env`, Docker volumes, IDE/OS clutter)
- [x] `.env` file created with all core credentials/ports (Postgres x2, MinIO, Airflow, Kafka)

### Core Infrastructure (docker-compose.yml)
- [x] Warehouse Postgres — running
- [x] Airflow Postgres (separate metadata DB) — running
- [x] MinIO (object storage) — running, console working on port 9001
  - Resolved image issues: `minio/minio` repo archived/pull-blocked →
    switched to `bitnamilegacy/minio:2025.7.23-debian-12-r5`
  - Had to explicitly set `command: minio server ... --console-address ":9001"`
    to get the WebUI to actually bind
- [x] Kafka + Zookeeper — running
  - Hit a `NodeExistsException` crash from a stale Zookeeper broker
    registration after repeated container restarts; resolved by retrying
    `docker compose up -d kafka` (stale session expired)
- [x] Airflow webserver + scheduler — running
  - Required manual one-time `airflow db init` (metadata DB wasn't
    auto-initialized)
  - Required manual `airflow users create` for admin login
- [x] Verified both web UIs load and function:
  - Airflow UI (`localhost:8080`) — login works, DAGs page loads
  - MinIO Console (`localhost:9001`) — login works, `raw-data` bucket visible

### Data Generators
- [x] **Step 1 — Master data generator** (`generate_master_data.py`)
  - 1,000 fake customers (India-specific via Faker `en_IN` locale)
  - 200 fake products across 7 categories
  - Output: `customers.csv`, `products.csv`
- [x] **Step 2 — Daily batch generator** (`generate_daily_batch.py`)
  - Reads master data, generates 150 daily orders + 200 inventory snapshots
  - Realistic weighted order status (85% completed / 10% cancelled / 5% returned)
  - Output: `orders_<date>.csv`, `inventory_<date>.csv`
- [x] **Step 3 — Kafka clickstream producer** (`clickstream_producer.py`)
  - Streams fake clickstream events continuously to Kafka topic
    `clickstream-events`
  - Weighted realistic event funnel (page views most common, purchases rarest)
  - Confirmed sending events successfully after Kafka stabilized
  - Ran for ~15-20 seconds and stopped cleanly with Ctrl+C

- [x] **Step 4 — Batch loader** (`load_to_minio.py`)
  - Pushes generator CSV output (customers, products, orders, inventory)
    into the MinIO `raw-data` bucket
  - Master data → fixed `reference/` path; daily data → date-partitioned
    paths (`orders/<date>/`, `inventory/<date>/`)
  - Revised to accept a `--date` argument (defaults to today) instead of
    hardcoding "today" — needed since Airflow will call this for specific
    scheduled dates, not just whenever the script happens to run
  - Added `--reference-only` flag and graceful missing-file handling
    (skips + warns instead of crashing)
  - Confirmed all 4 files uploaded successfully to correctly partitioned
    paths in the `raw-data` bucket

### Airflow Environment Upgrade
- [x] **Step 5 (setup) — Custom Airflow image**
  - Added `airflow/Dockerfile` extending `apache/airflow:2.9.0` with
    project dependencies (`faker`, `pandas`, `minio`, `kafka-python`)
    installed via `airflow/requirements.txt`
  - Updated `docker-compose.yml` so `airflow-webserver` and
    `airflow-scheduler` now `build` from this Dockerfile instead of
    pulling the plain base image
  - Added volume mounts so Airflow containers can see the actual project
    scripts (`data-generator/`, `ingestion/`) live, without rebuilding the
    image on every script change
  - Verified: all 7 containers up, and `faker`/`pandas`/`minio` all
    import successfully inside the Airflow container

- [x] **Step 5 — Airflow DAG** (`ecommerce_batch_pipeline.py`)
  - Defines a 2-task pipeline: `generate_daily_data >> load_to_minio`
  - Scheduled `@daily`, `catchup=False`, both tasks run via `BashOperator`
  - Uses Airflow's `{{ ds }}` templating so both tasks agree on the same
    logical run date
  - Had to add a `--date` argument to `generate_daily_batch.py` too (same
    pattern as the loader) so both tasks use the DAG's logical date
    instead of one of them silently using the real "today"
  - **Debugged a chain of 3 separate issues to get this working:**
    1. DAG didn't appear in UI → was just paused by default (Airflow's
       safety default for newly-added DAGs); fixed by unpausing
    2. Task logs showed a 403 Forbidden error → webserver and scheduler
       containers each had a different auto-generated secret key, so they
       couldn't authenticate to fetch each other's logs; fixed by setting
       an explicit shared `AIRFLOW__WEBSERVER__SECRET_KEY` in `.env` /
       `docker-compose.yml`
    3. Real error once visible: `load_to_minio.py` was connecting to
       `localhost:9000`, which inside the Airflow container refers to the
       Airflow container itself, not MinIO — fixed by switching to
       MinIO's Docker Compose **service name** (`minio:9000`), since
       containers reach each other by service name on the shared Compose
       network, not `localhost`
  - Confirmed: both tasks show `success` end-to-end after a manual trigger

### Spark Cluster
- [x] **Step 6 (setup) — Spark master + worker added to docker-compose.yml**
  - Initially tried `bitnami/spark:3.5`, hit the same archived-image issue
    as MinIO earlier (`bitnami/spark` now has zero published tags)
  - Switched to the **official `apache/spark:3.5.0`** image instead —
    more actively maintained, avoids relying on Bitnami entirely going
    forward
  - Official image needed explicit `spark-class` commands to start
    Master/Worker roles (no `SPARK_MODE` convenience env var like
    Bitnami had); ran as `user: root` to avoid volume permission issues
  - Mounted `./spark-jobs` into both containers so job scripts are
    live-linked, same pattern as the Airflow script mounts
  - Verified via Spark Master UI (`localhost:8081`): 1 worker connected,
    status ALIVE, 12 cores / 6.6 GiB available
  - Note: worker resource limits aren't capped yet (official image lacks
    Bitnami's `SPARK_WORKER_MEMORY`/`CORES` shortcuts) — fine for now,
    revisit if the machine feels strained running everything together

- [x] **Step 6 — Spark cleaning job** (`clean_orders_inventory.py`)
  - Reads raw orders/inventory CSVs from MinIO (`s3a://raw-data/orders/...`,
    `.../inventory/...`) using Spark's S3A connector
  - Cleans both datasets: drops duplicates (by order_id / product_id +
    snapshot_date), drops rows missing critical keys, filters out
    logically invalid rows (negative amounts/stock), standardizes
    order_status casing, parses order_date properly
  - Writes cleaned output as **Parquet** (not CSV) to a new `silver/`
    prefix in the same bucket — this is the project's Silver layer
  - Run via `spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,
    com.amazonaws:aws-java-sdk-bundle:1.12.262` so Spark can speak the S3
    protocol MinIO uses; packages are cached in the container after first
    download (~5 min first time, instant after)
  - Confirmed: `Cleaned orders: 150 -> 150` and
    `Cleaned inventory: 200 -> 200`, Parquet files written to
    `s3a://raw-data/silver/orders/2026-10-03/` and
    `.../silver/inventory/2026-10-03/`
  - Hit one setup issue along the way: tried a date (`2026-10-05`) that
    had never actually been loaded into MinIO — `PATH_NOT_FOUND` error;
    resolved by checking MinIO directly for which dates actually have
    data before running the job

- [x] **Step 7 — Wired Spark into the Airflow DAG** (`clean_with_spark` task)
  - DAG is now a full 3-task chain:
    `generate_daily_data >> load_to_minio >> clean_with_spark`
  - `clean_with_spark` runs `docker exec spark-master spark-submit ...`
    from inside the Airflow container — meaning Airflow now triggers
    Spark jobs running in a *separate* container automatically, daily
  - **Debugged a 2-step chain to get this working:**
    1. `Cannot connect to the Docker daemon` — the Airflow container had
       no access to the host's Docker daemon at all; fixed by mounting
       `/var/run/docker.sock` into both `airflow-webserver` and
       `airflow-scheduler` in `docker-compose.yml`
    2. `client version 1.41 is too old` — mounting the socket wasn't
       enough; the Airflow image also needed an actual `docker` CLI
       binary, and Debian's default `docker.io` package installed one
       too outdated to speak to Docker Desktop's API. Fixed by adding
       Docker's official APT repository to the Dockerfile and installing
       `docker-ce-cli` directly from it instead
  - Confirmed: full pipeline runs automatically end-to-end with zero
    manual steps — `Cleaned inventory: 200 raw -> 200 after cleaning`
    written to the Silver layer, triggered entirely by Airflow

---

## 🚧 Not Started Yet
- [ ] dbt project — star schema modeling (Silver → Gold)
- [ ] SCD Type 2 implementation for product price history
- [ ] Spark Structured Streaming job for live clickstream metrics
- [ ] Great Expectations data quality suite
- [ ] Warehouse loading (Gold layer → Postgres)
- [ ] Metabase/Superset dashboard setup
- [ ] Architecture diagram + final README polish

---

## Key Lessons / Gotchas Hit So Far

1. **Docker image registries change often** — `minio/minio` got archived
   mid-project; always have a fallback image source in mind (Docker Hub vs
   Quay, pinned tags vs `latest`).
2. **Airflow needs manual DB init** — `apache/airflow` images don't
   auto-initialize their metadata database or create an admin user; both are
   one-time `docker compose run` commands.
3. **Kafka + Zookeeper can leave stale state** — repeated container
   stop/start cycles without clean shutdowns can cause broker registration
   conflicts in Zookeeper; usually self-resolves on retry.
4. **Flaky wifi during large image pulls** — Airflow/Kafka images are
   300–450MB each; interrupted pulls resume via Docker's layer cache, so
   just retry rather than starting over.
5. **Scripts that will be scheduled need defensive design early** — a
   script that assumes "today" and crashes on a missing file works fine
   run manually, but breaks the moment Airflow needs to backfill or rerun
   a specific date. Building in date parameters and graceful skip/warn
   behavior now avoids a rewrite later.
6. **`localhost` means something different inside every container** — a
   script that correctly used `localhost:9000` when run directly on
   Windows failed inside the Airflow container, because `localhost` there
   points to the Airflow container itself. Cross-container calls in
   Docker Compose must use the other service's **service name** (e.g.
   `minio`, `kafka`) instead, since Compose provides internal DNS for that.
7. **Multi-container Airflow needs an explicit shared secret key** — by
   default each Airflow component (webserver, scheduler) generates its
   own random key, which breaks their ability to fetch each other's logs
   (shows as a 403 error, not a task failure). Setting
   `AIRFLOW__WEBSERVER__SECRET_KEY` explicitly for both fixes this.
8. **Bitnami images are becoming unreliable in general** — after MinIO's
   archival, `bitnami/spark` also now has zero published tags on Docker
   Hub. Going forward, prefer official/vendor-maintained images
   (`apache/spark`, etc.) over Bitnami wrappers where one exists, to avoid
   repeating this debugging cycle for every new tool added.
9. **Spark's S3 connector needs version-matched JARs** — `hadoop-aws` and
   `aws-java-sdk-bundle` versions must correspond to the Spark/Hadoop
   build in use (here: `hadoop-aws:3.3.4` + `aws-java-sdk-bundle:1.12.262`
   for Spark 3.5.0). Mismatched versions are a common, hard-to-diagnose
   source of Spark+S3/MinIO failures.
10. **Always verify data actually exists before processing it** — ran the
    Spark job against a date that was never loaded into MinIO, producing
    a `PATH_NOT_FOUND` error. Checking the data lake directly (or listing
    available partitions programmatically) before running a job avoids
    wasted debugging time chasing a "bug" that's really just missing input.
11. **A container can't control sibling containers by default** — having
    Airflow run `docker exec spark-master ...` required explicitly
    mounting the host's Docker socket (`/var/run/docker.sock`) into the
    Airflow container. This "Docker-out-of-Docker" pattern works for a
    local project but is a known security tradeoff in real production
    setups (Airflow's `SparkSubmitOperator` or `DockerOperator` are the
    more proper alternatives).
12. **Mounting the Docker socket isn't enough on its own** — the
    container also needs an actual `docker` CLI binary matching the
    host daemon's API version. Debian's default `docker.io` package was
    too outdated; installing `docker-ce-cli` from Docker's official APT
    repo fixed the version mismatch.
