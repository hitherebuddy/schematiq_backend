#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Execute the Gunicorn server directly from within the same script
# using the Python interpreter from the virtual environment.
# This bypasses all PATH and environment isolation issues.
/opt/render/project/src/.venv/bin/python -m gunicorn --config gunicorn_config.py app:app