#!/bin/bash

# RootAI v3.0 Setup Script
# Automated setup for development and production environments

set -e

echo "========================================"
echo "RootAI v3.0 - Setup Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "✗ Python 3.9+ required. Current version: $python_version"
    exit 1
fi
echo "✓ Python version OK"
echo ""

# Ask for installation type
echo "Select installation type:"
echo "  1) Development (with test dependencies)"
echo "  2) Production (minimal dependencies)"
echo "  3) Demo (without GPU packages)"
echo ""
read -p "Enter choice [1-3]: " install_type

case $install_type in
    1)
        echo "Installing development dependencies..."
        pip install -e ".[dev]"
        ;;
    2)
        echo "Installing production dependencies..."
        pip install -e .
        ;;
    3)
        echo "Installing demo dependencies (CPU-only)..."
        pip install torch transformers fastapi uvicorn numpy scipy nltk sentencepiece pydantic
        echo "Note: Skipping faiss-gpu and camel-tools for demo"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "✓ Dependencies installed"
echo ""

# Fetch data
echo "Fetching initial data..."
cd data
./fetch.sh
cd ..
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data/cache
mkdir -p models
mkdir -p logs
echo "✓ Directories created"
echo ""

# Run quick test
echo "Running quick validation..."
./test_quick.sh
echo ""

# Summary
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "RootAI v3.0 is ready to use!"
echo ""
echo "Quick start:"
echo "  1. Run demo: python demo.py"
echo "  2. Run CLI: ./rootai_cli.py reason 'What is justice?'"
echo "  3. Start API: python api/fastapi_app.py"
echo "  4. Run tests: pytest tests/ -v"
echo "  5. Run benchmark: python benchmarks/semantic_mmlu.py"
echo ""
echo "Documentation:"
echo "  - README.md: Overview and usage"
echo "  - EXAMPLES.md: Code examples"
echo "  - DEPLOYMENT.md: GCP deployment guide"
echo ""
echo "For help: ./rootai_cli.py --help"
echo ""
