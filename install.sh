#!/bin/bash
set -e

WHL_URL="https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/deep_ai_analysis-0.1.0-py3-none-any.whl"

echo "Installing deep-ai-analysis..."

pip install "$WHL_URL"

echo ""
echo "Installation complete. Run 'deep-ai-analysis --help' to get started."
