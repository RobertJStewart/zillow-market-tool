#!/bin/bash

# Zillow Market Tool - Testing Startup Script
# This script sets up the virtual environment and runs the complete pipeline

set -e  # Exit on any error

echo "🚀 Starting Zillow Market Tool Testing Environment"
echo "=================================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment found"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if packages are installed
echo "📦 Checking dependencies..."
if ! python -c "import duckdb, geopandas, h3, pandas" 2>/dev/null; then
    echo "📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Create data directory if it doesn't exist
if [ ! -d "data_raw" ]; then
    echo "📁 Creating data_raw directory..."
    mkdir -p data_raw
fi

# Check if data files exist
if [ ! -f "data_raw/zhvi.csv" ] || [ ! -f "data_raw/zori.csv" ]; then
    echo "📥 Downloading Zillow data files..."
    curl -o data_raw/zhvi.csv https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
    curl -o data_raw/zori.csv https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_sa_month.csv
    echo "✅ Data files downloaded"
else
    echo "✅ Data files already exist"
fi

echo ""
echo "🎯 Running Zillow Market Tool Pipeline"
echo "======================================"

# Run the pipeline steps
echo "1️⃣ Running data ingestion..."
python ingest/zillow_ingest.py

echo ""
echo "2️⃣ Running SQL transformations..."
python transform/run_sql.py

echo ""
echo "3️⃣ Exporting GeoJSON..."
python transform/export_zip_geojson.py

echo ""
echo "4️⃣ Projecting to H3..."
python transform/project_to_h3.py

echo ""
echo "🎉 Pipeline completed successfully!"
echo "=================================="
echo "📊 Check the output files in the current directory"
echo "🌐 Open app/index.html in your browser to view the results"
echo ""
echo "💡 To deactivate the virtual environment, run: deactivate"
