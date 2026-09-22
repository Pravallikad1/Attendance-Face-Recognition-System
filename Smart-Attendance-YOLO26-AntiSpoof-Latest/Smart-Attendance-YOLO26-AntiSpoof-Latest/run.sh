#!/usr/bin/env bash
echo "=========================================================="
echo " Starting Smart Attendance System Server (Port 8000)...   "
echo "=========================================================="

if [ -f "./.venv/bin/uvicorn" ]; then
    ./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi
