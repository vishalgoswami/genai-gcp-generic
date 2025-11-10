#!/bin/bash

# Custom Scores Setup Script

echo "=================================================="
echo "  Custom Scores Setup"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Please create .env file:"
    echo "  1. Copy the example: cp .env.example .env"
    echo "  2. Get your Langfuse keys from: https://us.cloud.langfuse.com/settings"
    echo "  3. Update LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env"
    echo ""
    exit 1
fi

# Check if credentials are set
source .env

if [ "$LANGFUSE_PUBLIC_KEY" = "pk-lf-your-public-key-here" ] || [ -z "$LANGFUSE_PUBLIC_KEY" ]; then
    echo "⚠️  LANGFUSE_PUBLIC_KEY not configured in .env"
    echo ""
    echo "Please update your .env file with actual credentials:"
    echo "  Get your keys from: https://us.cloud.langfuse.com/settings"
    echo ""
    exit 1
fi

if [ "$LANGFUSE_SECRET_KEY" = "sk-lf-your-secret-key-here" ] || [ -z "$LANGFUSE_SECRET_KEY" ]; then
    echo "⚠️  LANGFUSE_SECRET_KEY not configured in .env"
    echo ""
    echo "Please update your .env file with actual credentials:"
    echo "  Get your keys from: https://us.cloud.langfuse.com/settings"
    echo ""
    exit 1
fi

echo "✅ Environment configured correctly!"
echo ""
echo "You can now run:"
echo "  python custom_scoring.py --limit 10"
echo ""
