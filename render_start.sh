#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

echo "--- Creating local virtual environment ---"
python -m venv venv

echo "--- Installing dependencies using the venv's pip ---"
./venv/bin/pip install -r requirements.txt

echo "--- Starting Gunicorn Server using the venv's python and -m flag ---"
./venv/bin/python -m gunicorn --config gunicorn_config.py app:app