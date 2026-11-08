
from datetime import timedelta

import pendulum

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="ecommerce_etl_pipeline",

    description=(
        "Daily E-Commerce ETL Pipeline "
        "with PostgreSQL integration"
    ),

    start_date=pendulum.datetime(
        2026, 11, 1,
        tz="Asia/Jakarta",
    ),

    schedule="0 2 * * *",

    catchup=False,

    max_active_runs=1,

    default_args={
        "owner": "data-engineering",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(hours=2),
    },

    tags=["ecommerce", "etl", "postgresql"],

) as dag:

    check_source = BashOperator(
        task_id="check_source",

        bash_command=(
            'test -f "/opt/project/data/raw/Online Retail.xlsx"'
        ),
    )

    run_etl_pipeline = BashOperator(
        task_id="run_etl_pipeline",

        bash_command=(
            "python -m ecommerce_pipeline.pipeline"
        ),

        cwd="/opt/project",
    )

    verify_database = BashOperator(
        task_id="verify_database",

        bash_command=(
            "python scripts/verify_database.py"
        ),

        cwd="/opt/project",
    )

    check_source >> run_etl_pipeline >> verify_database
