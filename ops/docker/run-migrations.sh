#!/bin/sh
set -eu

python - <<'PY'
import os

import psycopg


database_url = os.environ["INVESTOR_DATABASE_URL"]
if database_url.startswith("postgresql+psycopg://"):
    database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)

with psycopg.connect(database_url, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(64) NOT NULL
            )
            """
        )
        cur.execute(
            """
            ALTER TABLE alembic_version
            ALTER COLUMN version_num TYPE VARCHAR(64)
            """
        )
PY

exec alembic upgrade head
