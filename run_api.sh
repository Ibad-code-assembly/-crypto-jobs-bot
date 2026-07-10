#!/bin/bash

# Run FastAPI backend server
echo "🚀 Starting Crypto Jobs API..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
