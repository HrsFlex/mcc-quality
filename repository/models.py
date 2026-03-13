"""
models.py — Database schema DDL.
SQLite DDL is used locally; Snowflake equivalents are documented below each table.
"""

QUALITY_INCIDENTS_DDL = """
CREATE TABLE IF NOT EXISTS quality_incidents (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id      TEXT    NOT NULL,
    source               TEXT    NOT NULL,
    plant                TEXT    NOT NULL,
    customer             TEXT    NOT NULL,
    incident_date        TEXT,           -- ISO8601 date string
    defect_category      TEXT,
    credit_requested_usd REAL    DEFAULT 0.0,
    qty_affected         REAL    DEFAULT 0.0,
    raw_source_file      TEXT,
    loaded_at            TEXT    DEFAULT (datetime('now'))
);
"""
# Snowflake equivalent (for future migration):
# CREATE TABLE IF NOT EXISTS QUALITY_DB.PUBLIC.quality_incidents (
#     id                   NUMBER AUTOINCREMENT PRIMARY KEY,
#     pipeline_run_id      VARCHAR,
#     source               VARCHAR,
#     plant                VARCHAR,
#     customer             VARCHAR,
#     incident_date        DATE,
#     defect_category      VARCHAR,
#     credit_requested_usd FLOAT,
#     qty_affected         FLOAT,
#     raw_source_file      VARCHAR,
#     loaded_at            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
# );

DIM_PLANT_DDL = """
CREATE TABLE IF NOT EXISTS dim_plant (
    plant_name   TEXT PRIMARY KEY,
    region       TEXT,
    country      TEXT,
    erp_system   TEXT,
    currency     TEXT    DEFAULT 'USD'
);
"""

DIM_CUSTOMER_DDL = """
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_name  TEXT PRIMARY KEY,
    risk_tier      TEXT    DEFAULT 'Low',
    updated_at     TEXT    DEFAULT (datetime('now'))
);
"""

PIPELINE_RUN_LOG_DDL = """
CREATE TABLE IF NOT EXISTS pipeline_run_log (
    run_id          TEXT    PRIMARY KEY,
    started_at      TEXT,
    finished_at     TEXT,
    status          TEXT,   -- SUCCESS | PARTIAL | FAILED
    total_rows      INTEGER DEFAULT 0,
    sources_loaded  TEXT,   -- comma-separated source keys
    error_message   TEXT
);
"""

ALL_DDL = [
    QUALITY_INCIDENTS_DDL,
    DIM_PLANT_DDL,
    DIM_CUSTOMER_DDL,
    PIPELINE_RUN_LOG_DDL,
]

# Seed data for dim_plant
PLANT_SEED_DATA = [
    {"plant_name": "Rochester",             "region": "Northeast", "country": "US",  "erp_system": "Fusion",  "currency": "USD"},
    {"plant_name": "OAK CREEK PLANT",       "region": "Midwest",   "country": "US",  "erp_system": "Vision",  "currency": "USD"},
    {"plant_name": "MASON PLANT",           "region": "Midwest",   "country": "US",  "erp_system": "Vision",  "currency": "USD"},
    {"plant_name": "MCC Louisville",        "region": "Midwest",   "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Elkton",            "region": "South",     "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Napa",              "region": "West",      "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Clarksville",       "region": "South",     "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Scottsburg",        "region": "Midwest",   "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Algoma",            "region": "Midwest",   "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Batavia",           "region": "Northeast", "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Knoxville",         "region": "South",     "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Lafayette Hill",    "region": "Northeast", "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Winona",            "region": "Midwest",   "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC York",              "region": "Northeast", "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Fullerton",         "region": "West",      "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Neenah",            "region": "Midwest",   "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Chesapeake",        "region": "South",     "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Humacao PR",        "region": "Caribbean", "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC San Luis Obispo",   "region": "West",      "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Asheville",         "region": "South",     "country": "US",  "erp_system": "Radius",  "currency": "USD"},
    {"plant_name": "MCC Monterrey",         "region": "North",     "country": "MX",  "erp_system": "Radius",  "currency": "MXN"},
    {"plant_name": "MCC Guadalajara",       "region": "West",      "country": "MX",  "erp_system": "Radius",  "currency": "MXN"},
    {"plant_name": "MCC Montreal",          "region": "Quebec",    "country": "CA",  "erp_system": "Radius",  "currency": "CAD"},
    {"plant_name": "Bowling Green Plant",   "region": "South",     "country": "US",  "erp_system": "OBI",     "currency": "USD"},
    {"plant_name": "Fountain Inn Plant",    "region": "South",     "country": "US",  "erp_system": "OBI",     "currency": "USD"},
    {"plant_name": "Fort Worth Plant",      "region": "South",     "country": "US",  "erp_system": "OBI",     "currency": "USD"},
    {"plant_name": "Niles Plant",           "region": "Midwest",   "country": "US",  "erp_system": "OBI",     "currency": "USD"},
    {"plant_name": "Tyrone Plant",          "region": "Northeast", "country": "US",  "erp_system": "OBI",     "currency": "USD"},
    {"plant_name": "Provo Plant",           "region": "West",      "country": "US",  "erp_system": "OBI",     "currency": "USD"},
    {"plant_name": "Waukesha Plant",        "region": "Midwest",   "country": "US",  "erp_system": "OBI",     "currency": "USD"},
]
