"""
db.py — Database connection management.
Returns a SQLite connection locally; will return a Snowflake connector when
USE_SNOWFLAKE=True is set in config.py.
"""
import sqlite3
import logging
import os
import sys

# Ensure the pipeline package root is in sys.path when called directly
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

from config import DB_PATH, USE_SNOWFLAKE, SNOWFLAKE
from repository.models import ALL_DDL, PLANT_SEED_DATA

logger = logging.getLogger(__name__)


def get_connection():
    """
    Returns an active database connection.
    - SQLite when USE_SNOWFLAKE=False (default)
    - Snowflake connector when USE_SNOWFLAKE=True
    """
    if USE_SNOWFLAKE:
        try:
            import snowflake.connector
            conn = snowflake.connector.connect(
                account=SNOWFLAKE["account"],
                user=SNOWFLAKE["user"],
                password=SNOWFLAKE["password"],
                database=SNOWFLAKE["database"],
                schema=SNOWFLAKE["schema"],
                warehouse=SNOWFLAKE["warehouse"],
            )
            logger.info("[DB] Connected to Snowflake")
            return conn
        except ImportError:
            raise RuntimeError("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        logger.info(f"[DB] Connected to SQLite: {DB_PATH}")
        return conn


def init_db():
    """
    Create all tables (idempotent: CREATE IF NOT EXISTS).
    Seeds dim_plant on first run.
    """
    conn = get_connection()
    cur = conn.cursor()

    for ddl in ALL_DDL:
        cur.executescript(ddl)

    # Seed dim_plant (ignore conflicts on existing rows)
    for row in PLANT_SEED_DATA:
        cur.execute(
            """INSERT OR IGNORE INTO dim_plant (plant_name, region, country, erp_system, currency)
               VALUES (:plant_name, :region, :country, :erp_system, :currency)""",
            row,
        )

    conn.commit()
    logger.info("[DB] Schema initialised and dim_plant seeded")
    return conn
