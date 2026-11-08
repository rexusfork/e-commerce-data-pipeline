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
