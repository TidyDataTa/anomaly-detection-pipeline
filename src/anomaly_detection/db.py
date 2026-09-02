"""Warehouse access: read metric series, write detection results.

Two connection paths are supported so the same code runs in both places it
needs to: an Airflow connection id when scheduled, a plain DSN when run by
hand. Credentials never appear in the source.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

import pandas as pd

logger = logging.getLogger(__name__)


@contextmanager
def connect(postgres_conn_id: str | None = None, database_url: str | None = None) -> Iterator:
    """Yield a PostgreSQL connection with autocommit enabled.

    Prefers the Airflow connection id when one is configured, so the DAG never
    has to carry a DSN of its own.
    """
    if postgres_conn_id:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        connection = PostgresHook(postgres_conn_id=postgres_conn_id).get_conn()
    elif database_url:
        import psycopg2

        connection = psycopg2.connect(database_url)
    else:
        raise ValueError(
            "No database configured: set ANOMALY_POSTGRES_CONN_ID (Airflow) "
            "or ANOMALY_DATABASE_URL (standalone)."
        )

    connection.autocommit = True
    try:
        yield connection
    finally:
        connection.close()


def read_sql(cursor, query: str) -> pd.DataFrame:
    """Run ``query`` and return the result as a DataFrame."""
    cursor.execute(query)
    columns = [description[0] for description in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def ensure_table(cursor, schema: str, table: str, columns: Sequence[tuple[str, str]]) -> None:
    """Create ``schema.table`` if it does not exist yet."""
    definition = ",\n    ".join(f"{name} {type_}" for name, type_ in columns)
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {schema}.{table} (\n    {definition}\n);")


def upsert_by_pointer(
    cursor,
    frame: pd.DataFrame,
    schema: str,
    table: str,
    pointer_column: str,
) -> int:
    """Replace the rows of ``frame``'s pointer values, then insert the frame.

    The pipeline is idempotent by day: re-running it for the same date first
    deletes that date's rows, so a retry never duplicates results.
    """
    if frame.empty:
        logger.info("%s.%s: nothing to write", schema, table)
        return 0

    pointers = sorted(set(frame[pointer_column].tolist()))
    cursor.execute(
        f"DELETE FROM {schema}.{table} WHERE {pointer_column} = ANY(%s);",
        (pointers,),
    )

    columns = list(frame.columns)
    placeholders = ", ".join(["%s"] * len(columns))
    statement = f"INSERT INTO {schema}.{table} ({', '.join(columns)}) VALUES ({placeholders});"
    rows = [tuple(row) for row in frame.itertuples(index=False, name=None)]
    cursor.executemany(statement, rows)

    logger.info("%s.%s: wrote %d row(s)", schema, table, len(rows))
    return len(rows)


def grant_read(cursor, schema: str, role: str) -> None:
    """Grant SELECT on the result schema to the BI role."""
    cursor.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {role};")
