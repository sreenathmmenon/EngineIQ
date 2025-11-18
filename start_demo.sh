#!/bin/bash

# EngineIQ Demo Startup Script

echo "======================================================================"
echo "🚀 EngineIQ Demo - Quick Start"
echo "======================================================================"
echo ""

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY not set"
    echo ""
    read -p "Enter your Google Gemini API key (or press Enter to use mock): " api_key
    if [ -n "$api_key" ]; then
        export GOOGLE_API_KEY="$api_key"
        echo "✓ API key set for this session"
    else
        echo "⚠️  Using mock embeddings (limited functionality)"
    fi
    echo ""
fi

# Check if Qdrant is running
echo "Checking Qdrant..."
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "✓ Qdrant is running"
else
    echo "❌ Qdrant is not running"
    echo ""
    echo "Starting Qdrant..."
    docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
    echo "⏳ Waiting for Qdrant to start..."
    sleep 5
fi

echo ""
echo "======================================================================"
echo "Starting EngineIQ API Server..."
echo "======================================================================"
echo ""

# Start the API server
python3 backend/api/server.py
