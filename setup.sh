#!/bin/bash
# Existing example files are never replaced.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys, sqlite3; assert sys.version_info >= (3, 9), "需要 Python 3.9+"; print("SQLite", sqlite3.sqlite_version)'
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
if [ ! -f examples/api_metrics.csv ]; then
    .venv/bin/python examples/make_api_data.py
fi
if [ ! -f examples/api_metrics.db ]; then
    .venv/bin/python csv2db.py import examples/api_metrics.csv examples/api_metrics.db --schema examples/api_metrics.schema.json
fi
.venv/bin/python csv2db.py query examples/api_metrics.db 'SELECT COUNT(*) AS record_count FROM api_metrics'
