#!/bin/bash

echo "🗺️ Getting ZIP code coordinates..."
echo "=================================="

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run start_testing.sh first."
    exit 1
fi

# Install requests if not already installed
echo "📦 Installing requests..."
pip install requests

# Run the coordinate fetching script
echo "📍 Fetching coordinates (this may take a while)..."
python transform/fetch_zip_coordinates.py

# Update the GeoJSON with real coordinates
echo "🔄 Updating GeoJSON with real coordinates..."
python transform/update_geojson_with_coordinates.py

echo "✅ Coordinate fetching complete!"
echo "🌐 Refresh your browser to see the updated map with real locations."
