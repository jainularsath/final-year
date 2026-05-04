#!/bin/bash
# TN Events - Start all 3 servers (macOS/Linux)
echo "🚀 Starting TN Events Backend..."

cd "$(dirname "$0")"

# Activate venv if exists
[ -f "venv/bin/activate" ] && source venv/bin/activate

echo "[1/3] User Server → http://localhost:3000"
cd server_user && python app.py &
cd ..

sleep 1

echo "[2/3] Vendor Server → http://localhost:3001"
cd server_vendor && python app.py &
cd ..

sleep 1

echo "[3/3] Admin Server → http://localhost:3002"
cd server_admin && python app.py &
cd ..

echo ""
echo "✅ All servers running!"
echo "  User   → http://localhost:3000"
echo "  Vendor → http://localhost:3001"
echo "  Admin  → http://localhost:3002"
echo ""
echo "Press Ctrl+C to stop all servers."
wait
