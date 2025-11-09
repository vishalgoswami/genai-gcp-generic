#!/bin/bash
# Launch script for Streamlit ADK Agent Chat UI

echo "🚀 Starting ADK Agent Chat UI..."
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "../../.venv" ]; then
    echo "❌ Virtual environment not found at ../../.venv"
    echo "Please create a virtual environment first:"
    echo "  cd /Users/vishal/genai/1"
    echo "  python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source ../../.venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check authentication
echo "🔐 Checking Google Cloud authentication..."
if ! gcloud auth application-default print-access-token &> /dev/null; then
    echo "⚠️  Not authenticated. Running: gcloud auth application-default login"
    gcloud auth application-default login
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "⚙️  Loading environment from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "ℹ️  No .env file found, using defaults"
fi

echo ""
echo "✅ Ready to launch!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Launch Streamlit
streamlit run app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false
