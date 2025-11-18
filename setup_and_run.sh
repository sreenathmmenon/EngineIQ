#!/bin/bash

# EngineIQ Setup and Run Script

echo "======================================================================"
echo "EngineIQ Setup - Real Embeddings"
echo "======================================================================"
echo ""

# Step 1: Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY not set in environment"
    echo ""
    echo "Please set it now:"
    echo ""
    read -p "Enter your Google Gemini API key: " api_key
    export GOOGLE_API_KEY="$api_key"
    echo ""
    echo "✓ GOOGLE_API_KEY set for this session"
else
    echo "✓ GOOGLE_API_KEY already set"
fi

echo ""
echo "======================================================================"
echo "Step 1: Clear old data and regenerate with real embeddings"
echo "======================================================================"
echo ""

# Optional: Clear Qdrant collections for fresh start
read -p "Clear existing data and start fresh? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Reinitializing collections..."
    python3 -c "from backend.services.qdrant_service import QdrantService; s = QdrantService(); s.initialize_collections()"
fi

echo ""
echo "Generating demo data with REAL Gemini embeddings..."
echo ""
python3 backend/scripts/generate_demo_data.py

echo ""
echo "======================================================================"
echo "✅ Setup Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Your data is now in Qdrant with real embeddings"
echo "2. Ready to build API server for queries"
echo ""
