# Apache Airflow Orchestration

## Overview

Apache Airflow is used to orchestrate the E-Commerce ETL Pipeline and monitor scheduled executions.

## Technology

- Apache Airflow 3.1.7
- Docker Compose
- Python and Pandas
- PostgreSQL
- BashOperator

## Architecture

The orchestration layer consists of three dependent tasks:

```text
check_source
    |
    v
run_etl_pipeline
    |
    v
verify_database
```

## DAG Configuration

| Configuration | Value |
|---|---|
| DAG ID | ecommerce_etl_pipeline |
| Schedule | Daily, 02:00 Asia/Jakarta |
| Catchup | Disabled |
| Max Active Runs | 1 |
| Retries | 2 |
| Retry Delay | 5 minutes |
| Task Timeout | 2 hours |

## Execution Flow

1. Check that the source Excel dataset is available.
2. Run the existing Python ETL pipeline.
3. Verify that the PostgreSQL database contains loaded data and a successful execution record.

The Python ETL pipeline retains responsibility for incremental file detection, transformation, database loading, data quality validation, and execution tracking.

## Running Locally

Start the infrastructure:

```bash
docker compose up -d --build
```

Open the Airflow UI at `http://localhost:8080`.

Find the `ecommerce_etl_pipeline` DAG and trigger it manually, or activate scheduling.

## Monitoring

Airflow provides task execution history, status, duration, logs, retry attempts, and workflow visualization.

Application-level metrics are separately stored in PostgreSQL in the `pipeline_runs` table.

## Failure Handling

Failed tasks are automatically retried according to the DAG configuration.

The Python pipeline handles database transaction rollback and application-level failure tracking.

## Limitations

- Airflow standalone is intended for local development.
- Airflow metadata uses local SQLite storage.
- The current DAG executes the complete ETL as one task.
- File-level incremental processing does not support row-level updates.
- Basic database verification does not compare the current source checksum to the latest successful run.
- No alerting or distributed worker infrastructure has been configured.

## Future Improvements

- Separate extract, transform, and load into independent tasks.
- Add persistent intermediate datasets.
- Configure task-level metrics and alerts.
- Implement row-level incremental loading.
- Deploy Airflow using a production-oriented architecture.
