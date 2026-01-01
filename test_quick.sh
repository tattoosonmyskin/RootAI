#!/bin/bash

# RootAI v3.0 - Quick Test Script
# Tests basic functionality without requiring full dependencies

set -e

echo "========================================"
echo "RootAI v3.0 - Quick Test"
echo "========================================"
echo ""

# Test 1: Check Python syntax
echo "Test 1: Checking Python syntax..."
python3 -m py_compile src/core/graph_sharding.py
python3 -m py_compile src/core/root_reasoner.py
python3 -m py_compile api/fastapi_app.py
python3 -m py_compile benchmarks/semantic_mmlu.py
echo "✓ All Python files have valid syntax"
echo ""

# Test 2: Check file structure
echo "Test 2: Checking file structure..."
required_files=(
    "pyproject.toml"
    "Dockerfile"
    "docker-compose.yml"
    "src/core/graph_sharding.py"
    "src/core/root_reasoner.py"
    "api/fastapi_app.py"
    "benchmarks/semantic_mmlu.py"
    "data/fetch.sh"
    "rootai_cli.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ Missing: $file"
        exit 1
    fi
done
echo ""

# Test 3: Check executables
echo "Test 3: Checking executable permissions..."
if [ -x "data/fetch.sh" ]; then
    echo "✓ data/fetch.sh is executable"
else
    echo "✗ data/fetch.sh is not executable"
    chmod +x data/fetch.sh
    echo "  Fixed: Added executable permission"
fi

if [ -x "rootai_cli.py" ]; then
    echo "✓ rootai_cli.py is executable"
else
    echo "✗ rootai_cli.py is not executable"
    chmod +x rootai_cli.py
    echo "  Fixed: Added executable permission"
fi
echo ""

# Test 4: Check documentation
echo "Test 4: Checking documentation..."
doc_files=(
    "README.md"
    "DEPLOYMENT.md"
    "EXAMPLES.md"
    "CONTRIBUTING.md"
    "CHANGELOG.md"
    "LICENSE"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "! Optional doc missing: $file"
    fi
done
echo ""

# Test 5: Verify directory structure
echo "Test 5: Verifying directory structure..."
required_dirs=(
    "src"
    "src/core"
    "src/api"
    "api"
    "benchmarks"
    "data"
    "tests"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/"
    else
        echo "✗ Missing directory: $dir/"
        exit 1
    fi
done
echo ""

# Summary
echo "========================================"
echo "All Basic Tests Passed! ✓"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Install dependencies: pip install -e ."
echo "2. Fetch data: ./data/fetch.sh"
echo "3. Run unit tests: pytest tests/ -v"
echo "4. Start API: python api/fastapi_app.py"
echo "5. Run benchmark: python benchmarks/semantic_mmlu.py"
echo ""
echo "For deployment:"
echo "- Docker: docker build -t rootai:v3.0 ."
echo "- GCP: See DEPLOYMENT.md"
echo ""
