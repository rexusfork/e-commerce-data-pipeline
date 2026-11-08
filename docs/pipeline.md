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
