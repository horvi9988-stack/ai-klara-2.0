#!/usr/bin/env bash
# Start Klara AI Streamlit app on port 8501
# Usage: ./start.sh
set -euo pipefail
cd "$(dirname "$0")"
streamlit run streamlit_app.py --server.port=8501 --logger.level=info
