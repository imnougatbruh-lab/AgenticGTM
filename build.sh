#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting Production Build Pipeline..."

# Upgrade pip and install requirements
echo "📦 Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright Chromium and its Linux operating system dependencies
echo "🎭 Installing Playwright Chromium & OS dependencies..."
playwright install chromium

echo "🎯 Build pipeline completed successfully! App is ready for production start command."
