#!/bin/bash

echo "🚀 Setting up Note Recommendation System..."

# Create directory structure
echo "📁 Creating directories..."
mkdir -p config
mkdir -p database
mkdir -p models
mkdir -p services
mkdir -p data

# Create __init__.py files
touch config/__init__.py
touch database/__init__.py
touch models/__init__.py
touch services/__init__.py

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env file with your Neo4j credentials."
    echo "See .env.example for reference."
else
    echo "✓ .env file found"
fi

# Initialize data files
echo "📝 Initializing data files..."
echo '{"ab_test_a_like_count": 0, "ab_test_b_like_count": 0, "last_updated": "'$(date -Iseconds)'"}' > data/ab_test_counts.json
echo '[]' > data/ab_test_likes.json

echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your .env file with Neo4j credentials"
echo "2. Run: python database/init_mock_data.py"
echo "3. Start the server: python main.py"