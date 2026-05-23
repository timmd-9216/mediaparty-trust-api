#!/bin/bash
# Run the Laiaton web signature analyzer

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "Starting Laiaton Signature Analyzer..."
echo "Open http://localhost:8080 in your browser"
echo "Press Ctrl+C to stop"
echo ""

uv run uvicorn mediaparty_trust_api.web_signature.app:app --host 0.0.0.0 --port 8080 --reload
