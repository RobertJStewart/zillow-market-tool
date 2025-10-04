#!/bin/bash

echo "🏗️ Building Multi-Level Geographic Aggregation System"
echo "====================================================="

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

# Install additional dependencies
echo "📦 Installing additional dependencies..."
pip install requests

# Step 1: Get ZIP code coordinates (if not already done)
echo ""
echo "📍 Step 1: Getting ZIP code coordinates..."
if [ ! -f "data_demo/zip_coordinates.json" ]; then
    echo "🚀 Using fast coordinate fetching method..."
    python transform/fetch_zip_coordinates_fast.py
else
    echo "✅ ZIP coordinates already exist"
fi

# Step 2: Update GeoJSON with real coordinates
echo ""
echo "🔄 Step 2: Updating GeoJSON with real coordinates..."
python transform/update_geojson_with_coordinates.py

# Step 3: Create multi-level aggregation
echo ""
echo "🏗️ Step 3: Creating multi-level geographic aggregation..."
python transform/create_multi_level_aggregation.py

# Step 4: Verify files were created
echo ""
echo "✅ Step 4: Verifying output files..."
echo "📁 Checking for required files:"

required_files=(
    "data_demo/zip_coordinates.json"
    "data_demo/zip_latest.geojson"
    "data_demo/aggregated/regions.geojson"
    "data_demo/aggregated/state_regions.geojson"
    "data_demo/aggregated/states.geojson"
    "data_demo/aggregated/config.json"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = true ]; then
    echo ""
    echo "🎉 Multi-level system built successfully!"
    echo "========================================"
    echo "📊 Geographic levels available:"
    echo "  - Region level (zoom ≤ 4)"
    echo "  - State Region level (zoom ≤ 6)"
    echo "  - State level (zoom ≤ 8)"
    echo "  - ZIP code level (zoom ≤ 10)"
    echo ""
    echo "📈 Statistical methods available:"
    echo "  - Average, Median, Maximum, Minimum, Count"
    echo ""
    echo "🌐 Open index.html in your browser to see the new system!"
    echo "💡 The map will automatically switch geographic levels based on zoom"
else
    echo ""
    echo "❌ Some files are missing. Please check the errors above."
    exit 1
fi
