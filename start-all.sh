#!/bin/bash

echo "Starting TestFlow..."
echo ""

echo "[1/3] Starting Backend (Port 8000)..."
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 2

echo "[2/3] Starting Execution Engine..."
cd ../executor && python main.py &
EXECUTOR_PID=$!
sleep 2

echo "[3/3] Starting Frontend (Port 3002)..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!
sleep 2

echo ""
echo "============================================"
echo "All components started successfully!"
echo "============================================"
echo "- Backend API:    http://localhost:8000"
echo "- Executor:       Running as standalone app"
echo "- Frontend:       http://localhost:3002"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all components"

# Handle shutdown
trap "kill $BACKEND_PID $EXECUTOR_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Wait for any process to exit
wait -n
