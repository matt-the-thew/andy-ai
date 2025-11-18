#!/bin/bash

# Quick Start Script for Andy AI Bot
# This script sets up and runs the bot with best practices

set -e

echo "🤖 Andy AI Bot - Quick Start Setup"
echo "=================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found Python $python_version"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "✓ Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -r requirements.txt --quiet

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Create a .env file with:"
    echo "  DISCORD_API_TOKEN=your_token_here"
    echo "  OPENAI_API_KEY=your_key_here"
    echo "  LOG_LEVEL=INFO"
    exit 1
fi

echo "✓ Environment configured"
echo ""

# Run tests
echo "✓ Running tests..."
python -m pytest tests/ --quiet --tb=short

echo ""
echo "✨ All checks passed!"
echo ""
echo "Starting bot... Press Ctrl+C to stop"
echo ""

# Run the bot
python main.py
