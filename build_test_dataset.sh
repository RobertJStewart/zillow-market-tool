#!/bin/bash

echo "🧪 Building Focused Test Dataset"
echo "==============================="

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

# Run the test dataset creation
echo "🚀 Creating focused test dataset..."
python transform/create_test_dataset.py

echo ""
echo "✅ Test dataset created successfully!"
echo "📊 Dataset structure:"
echo "  - 1 Region (Northeast)"
echo "  - 2 State Regions (New England, Mid-Atlantic)"  
echo "  - 6 States (ME, MA, NH, NJ, NY, PA)"
echo "  - 15 ZIP codes (5 per state)"
echo ""
echo "🌐 Open index.html in your browser to test the system!"
echo "💡 This small dataset will load instantly and let you test all features!"
