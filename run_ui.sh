#!/bin/bash
# Streamlit UI起動スクリプト

# FastAPI URLを設定（環境変数で上書き可能）
export PAPERSMITH_API_URL=${PAPERSMITH_API_URL:-"http://localhost:8000"}

echo "Starting Papersmith Agent UI..."
echo "API URL: $PAPERSMITH_API_URL"
echo "UI will be available at: http://localhost:8501"
echo ""

# Streamlitを起動
streamlit run ui/app.py
