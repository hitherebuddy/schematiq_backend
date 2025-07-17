#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Installing Dependencies ---"
pip install -r requirements.txt

echo "--- Starting Gunicorn Server ---"
gunicorn --config gunicorn_config.py app:app