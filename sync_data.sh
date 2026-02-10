#!/bin/bash
echo "Running Backend..."
cd ../backend
python main.py

echo "Syncing data to Frontend..."
cp output/results.json ../frontend/public/

echo "Done!"