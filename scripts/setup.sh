#!/bin/bash
# Quick setup script for RetailFlow
set -e
echo "Setting up RetailFlow..."
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Done. Activate with: source venv/bin/activate"
echo "Download the M5 dataset from Kaggle into data/raw/"
