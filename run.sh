#!/bin/bash
# Sightline AI — one-click launcher
# Sets up a virtual environment (first run only) and starts the app.

set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment (first run only)..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

python3 sightline.py "$@"
