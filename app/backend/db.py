"""Databricks access for the Data Core Console.

Ambient app auth in the Databricks Apps runtime (WorkspaceClient() reads the
injected service-principal credentials); locally it falls back to the CLI
profile. All data access is via the SQL Statement Execution API against the
warehouse identified by DATABRICKS_WAREHOUSE_ID.
"""

import os
import functools

from databricks.sdk import WorkspaceClient

CATALOG = os.environ.get("DATA_CORE_CATALOG", "lr_serverless_aws_us_catalog")
SCHEMA_PATTERN = os.environ.get("DATA_CORE_SCHEMA_PATTERN", "bricksurance_{domain}")
# Default warehouse lets the app run locally against the demo workspace; in the
# deployed app DATABRICKS_WAREHOUSE_ID is injected from the sql-warehouse resource.
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "ab79eced8207d29b")
SERVING_ENDPOINT = os.environ.get("SERVING_ENDPOINT", "databricks-claude-sonnet-5")


@functools.lru_cache(maxsize=1)
def client() -> WorkspaceClient:
    # In the Apps runtime the ambient env configures the SP; locally the CLI
    # profile (DATABRICKS_CONFIG_PROFILE) is used.
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE")
    if profile and not os.environ.get("DATABRICKS_CLIENT_ID"):
        return WorkspaceClient(profile=profile)
    return WorkspaceClient()


def q(domain: str, name: str) -> str:
    return f"{CATALOG}.{SCHEMA_PATTERN.format(domain=domain)}.{name}"


def run_sql(sql: str):
    w = client()
    resp = w.statement_execution.execute_statement(
        statement=sql, warehouse_id=WAREHOUSE_ID, wait_timeout="50s")
    while resp.status.state.value in ("PENDING", "RUNNING"):
        resp = w.statement_execution.get_statement(resp.statement_id)
    if resp.status.state.value != "SUCCEEDED":
        raise RuntimeError(resp.status.error.message)
    return resp.result.data_array or []
