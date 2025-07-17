#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

echo "--- Installing dependencies using python -m pip ---"
python -m pip install -r requirements.txt

echo "--- Starting server with python -m gunicorn ---"
python -m gunicorn --config gunicorn_config.py app:app