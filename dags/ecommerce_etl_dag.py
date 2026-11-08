
from datetime import timedelta

import pendulum

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


import json
import logging
import os

from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


def send_failure_alert(context):
    """Send notification when an Airflow task fails."""

    webhook_url = os.getenv("ALERT_WEBHOOK_URL")

    if not webhook_url:
        logger.warning("Alert webhook not configured")
        return

    task_instance = context["task_instance"]

    dag_id = task_instance.dag_id
    task_id = task_instance.task_id
    run_id = context["run_id"]
    exception = context.get("exception")

    message = (
        "**Data Pipeline Failure**\n"
        f"DAG: {dag_id}\n"
        f"Task: {task_id}\n"
        f"Run: {run_id}\n"
        f"Error: {str(exception)[:300]}"
    )

    payload = json.dumps({
        "content": message[:1800]
    }).encode("utf-8")

    request = Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            logger.info(
                "Failure alert sent: HTTP %s",
                response.status,
            )
    except Exception:
        logger.exception("Failed to send alert")

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
    "on_failure_callback": send_failure_alert,
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
