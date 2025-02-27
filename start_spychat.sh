#!/bin/bash
echo "Installing requirements..."
pip3 install -r requirements.txt
echo "Starting SpyChat Server..."
cd "$(dirname "$0")"
python3 app.py 