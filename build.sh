#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install all dependencies from requirements.txt
pip install -r requirements.txt

# 2. The script finishes, and Render will use the "Start Command"
#    from the UI, which will now have access to the installed packages.