#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

echo "--- STARTING FORENSIC ANALYSIS SCRIPT ---"

echo "[DIAGNOSTIC] Current working directory: $(pwd)"
echo "[DIAGNOSTIC] Listing contents of current directory:"
ls -la

echo "[DIAGNOSTIC] Python version available: $(python --version)"

echo "[STEP 1] Creating local virtual environment 'venv'"
python -m venv venv
echo "[SUCCESS] Virtual environment created."

echo "[STEP 2] Attempting to install dependencies using the venv's pip..."
# We will add an explicit check to see if pip fails
if ./venv/bin/pip install -r requirements.txt; then
    echo "[SUCCESS] pip install command completed."
else
    echo "[FATAL] pip install command failed with exit code $?."
    exit 1
fi

echo "[STEP 3] Verifying installation by listing site-packages..."
# Find the site-packages directory automatically.
SITE_PACKAGES_DIR=$(find venv/lib -name "site-packages")
echo "[DIAGNOSTIC] Found site-packages directory at: $SITE_PACKAGES_DIR"
echo "[DIAGNOSTIC] Listing contents of site-packages:"
ls -la "$SITE_PACKAGES_DIR"

echo "[STEP 4] Verifying gunicorn installation explicitly..."
# Check if the gunicorn directory exists inside site-packages
if [ -d "$SITE_PACKAGES_DIR/gunicorn" ]; then
    echo "[SUCCESS] Gunicorn directory found in site-packages."
else
    echo "[FATAL] Gunicorn directory NOT found in site-packages. Installation failed silently."
    exit 1
fi

echo "[STEP 5] Attempting to start server..."
./venv/bin/python -m gunicorn --config gunicorn_config.py app:app

echo "--- SCRIPT COMPLETED ---"