#!/bin/bash

cd "$(dirname "$0")"

# Must be set before PyTorch initializes its thread pool (too late via .env)
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false

source venv/bin/activate

echo "Starting FastAPI on http://0.0.0.0:8000 ..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "Starting Streamlit on http://0.0.0.0:8501 ..."
streamlit run ui/app.py --server.address 0.0.0.0 --server.port 8501 &
UI_PID=$!

echo ""
echo "Both services running. Press Ctrl+C to stop."
echo "  API:  http://$(hostname -I | awk '{print $1}'):8000"
echo "  UI:   http://$(hostname -I | awk '{print $1}'):8501"
echo ""

trap "echo 'Stopping...'; kill $API_PID $UI_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
