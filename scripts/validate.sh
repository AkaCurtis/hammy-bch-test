#!/bin/bash
set -e

echo "Validating YAML files..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required"
    exit 1
fi

# Validate YAML parsing
python3 -c "
import yaml
import sys

files = [
    'umbrel-app-store.yml',
    'hammy-bch-solo-node/umbrel-app.yml',
    'hammy-bch-solo-node/docker-compose.yml'
]

for file in files:
    try:
        with open(file) as f:
            yaml.safe_load(f)
        print(f'✓ {file} is valid YAML')
    except Exception as e:
        print(f'✗ {file} has errors: {e}')
        sys.exit(1)
"

echo ""
echo "Validating Docker Compose config..."
cd hammy-bch-solo-node
docker compose config > /dev/null 2>&1 && echo "✓ Docker Compose config is valid" || echo "✗ Docker Compose config has errors"

echo ""
echo "Checking required files..."
required_files=(
    "icon.svg"
    "data/templates/bchn-entrypoint.sh"
    "data/templates/bitcoin.conf.template"
    "data/templates/ckpool.conf.template"
    "services/bchn/Dockerfile"
    "services/ckpool/Dockerfile"
    "web/Dockerfile"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file is missing"
        exit 1
    fi
done

echo ""
echo "All validations passed!"
