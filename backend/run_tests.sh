#!/bin/bash
# Script to run tests inside Docker container

echo "Installing test dependencies..."
pip install -q pytest pytest-flask pytest-cov pytest-mock faker

echo ""
echo "Running tests..."
pytest tests/ "$@"
