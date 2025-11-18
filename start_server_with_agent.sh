#!/bin/bash

# Start EngineIQ server with agent system enabled

echo "🚀 Starting EngineIQ with Agent System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Change to project directory
cd "$(dirname "$0")"

# Load API key from .env-droid
if [ -f ".env-droid" ]; then
    export GEMINI_API_KEY=$(grep GEMINI_API_KEY .env-droid | cut -d '=' -f2)
    echo "✓ API Key loaded from .env-droid"
    echo "  Key: ${GEMINI_API_KEY:0:20}..."
else
    echo "❌ Error: .env-droid file not found"
    echo "   Please create .env-droid with your GEMINI_API_KEY"
    exit 1
fi

# Check if API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY is empty"
    echo "   Please add GEMINI_API_KEY=your-key to .env-droid"
    exit 1
fi

echo ""
echo "🔷 Starting server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start server
python backend/api/server.py
