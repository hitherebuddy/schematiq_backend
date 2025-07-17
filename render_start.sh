#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

echo "--- RENDER_START.SH SCRIPT INITIATED ---"

# 1. Create a new, local virtual environment within the build directory.
#    This ensures we have full control and it's not a temporary venv.
python -m venv venv

# 2. Activate the virtual environment.
source venv/bin/activate

# 3. Install all dependencies into THIS specific virtual environment.
echo "--- Installing dependencies into local venv ---"
pip install -r requirements.txt

# 4. Start the Gunicorn server using the Python from THIS venv.
#    This is physically incapable of failing with "No module named gunicorn".
echo "--- Starting Gunicorn Server from local venv ---"
gunicorn --config gunicorn_config.py app:app