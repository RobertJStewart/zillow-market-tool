#!/bin/bash

# Simple script to activate the virtual environment
# Usage: source activate_env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./start_testing.sh first"
    return 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo "💡 Run 'deactivate' to exit the virtual environment"
