# ETL Pipeline Documentation

## 1. Data Source

The pipeline uses the Online Retail dataset provided by the UCI Machine Learning Repository.

- Source: https://archive.ics.uci.edu/dataset/352/online+retail
- Format: Excel (.xlsx)
- Records: 541,909
- Columns: 8
- License: CC BY 4.0

**Dataset Citation:** Chen, D. (2015). *Online Retail*. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33

## 2. Extraction Process

The extraction module is responsible for loading raw transaction data from Excel into a Pandas DataFrame.

### Workflow

1. Verify source file existence.
2. Read the Excel dataset.
3. Validate that the dataset is not empty.
4. Verify required columns.
5. Record extraction statistics.
6. Return the raw DataFrame for downstream processing.

## 3. Error Handling

The pipeline handles missing files, unreadable Excel data, empty datasets, and missing required columns.

## 4. Logging

The extraction process logs its execution status, source path, row count, column count, and estimated DataFrame memory usage.

## 5. Testing

Automated tests cover successful extraction, missing files, empty datasets, invalid schemas, and repeated invoice identifiers.

## 6. Next Steps

The extracted dataset will be passed to the transformation module for data cleaning, validation, and preparation before loading into PostgreSQL.


## Data Transformation

The transformation stage converts raw retail transaction records into validated analytical datasets.

### Transformation Rules

1. Remove exact duplicate rows.
2. Normalize text, numeric, and datetime columns.
3. Preserve transactions with missing customer identifiers.
4. Classify cancellation records using the invoice prefix `C`.
5. Reject invalid transaction records.
6. Calculate total transaction amounts.
7. Reconcile input records against transformation outputs.

### Data Outputs

| Dataset | Description |
|---|---|
| Sales | Valid transactions with positive quantity and unit price |
| Cancellations | Valid cancellation records with negative quantity |
| Rejected | Records that do not satisfy the defined validation rules |

### Data Quality Metrics

The transformation stage records:

- Total input rows
- Number of exact duplicate rows
- Number of valid sales rows
- Number of cancellation rows
- Number of rejected rows
- Number of output rows

A reconciliation check verifies that every input record is accounted for.

### Limitations

- Duplicate detection uses exact row equality and may not identify semantic duplicates.
- Cancellation records are classified but are not matched to their original transactions.
- Rejected records currently use a generic rejection reason.
- Monetary values are processed using floating-point numbers; financial precision can be improved using decimal types in a later iteration.
- Invalid or fractional customer identifiers require additional schema checks before integer conversion.

### Next Stage

Validated records will be loaded into PostgreSQL using separate tables for sales, cancellations, and rejected transactions.

## Data Loading — PostgreSQL

### Overview

The loading stage persists transformed transaction records into PostgreSQL using SQLAlchemy.

### Database Tables

- `sales`: Valid sales transaction line items.
- `cancellations`: Cancellation transaction line items.
- `rejected`: Invalid records preserved for auditing.

### Transaction Management

The loading process uses a single database transaction across all three tables. A failure during insertion triggers a rollback, preventing partial persistence.

### Idempotency

Each record receives a deterministic SHA-256 source fingerprint. PostgreSQL uses `ON CONFLICT DO NOTHING` to prevent duplicate insertion when the same records are processed again.

### Batch Processing

Records are inserted in batches of 1,000 within one database transaction.

### Integration Tests

Integration tests verify:

- Successful persistence across three tables.
- Idempotent repeated execution.
- Transaction rollback after database constraint violations.

### Known Limitations

- Content-based fingerprints cannot distinguish legitimate identical source rows.
- Existing records are not updated when source values change.
- Persisted row counts may include data from previous pipeline runs.
- Large datasets may require streaming, staging tables, or PostgreSQL COPY for better performance.
- Schema changes should eventually use versioned database migrations.

### Next Improvements

Introduce incremental loading, detailed data quality reasons, pipeline execution logs, monitoring, and orchestration.


## Step 5 — Incremental Processing and Execution Tracking

### Overview

The pipeline implements file-level incremental processing using SHA-256 checksums and PostgreSQL execution history.

### Incremental Processing

Before extraction, the pipeline calculates a checksum of the source file.

If a successful execution already exists for the same source and checksum, processing is skipped.

When the file changes, the pipeline performs extraction, transformation, and loading again. Previously inserted records are protected by deterministic record fingerprints and PostgreSQL conflict handling.

### Execution Tracking

Pipeline execution metadata is stored in the `pipeline_runs` table.

Supported statuses:

- RUNNING
- SUCCESS
- FAILED

Execution metrics include source row counts, transformation statistics, and stage durations.

### Transaction Management

Data loading and the transition to SUCCESS occur within the same PostgreSQL transaction.

Failed executions are recorded separately after the loading transaction is rolled back.

### Performance

Current optimizations include:

- Chunked SHA-256 calculation
- Skipping unchanged source files
- Batch database inserts
- Database indexes for execution lookup
- Measuring execution duration by pipeline stage

### Limitations

- The incremental mechanism operates at file level rather than row level.
- Changed files are fully extracted and transformed again.
- Existing source records are not updated or deleted.
- Concurrent executions are not yet coordinated.
- Unexpected process termination may leave RUNNING records.
- Record preparation still materializes data in memory.
- Pipeline runs skipped due to unchanged files are not persisted as separate execution records.

### Future Improvements

- Row-level incremental ingestion
- Source watermarks and checkpointing
- PostgreSQL COPY with staging tables
- UPSERT and source deletion handling
- Pipeline heartbeat and recovery
- Apache Airflow orchestration
- Data quality monitoring and alerting
