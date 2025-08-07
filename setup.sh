#!/bin/bash

echo "🌟 Smart Trip Scout AI Setup"
echo

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo
echo "Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env and add your API keys before running the app"
else
    echo "ℹ️  .env file already exists"
fi

echo
echo "🎉 Setup complete!"
echo
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run: python trip_scout.py"
echo
