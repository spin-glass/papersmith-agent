#!/bin/bash
# -*- coding: utf-8 -*-
# カバレッジレポート生成スクリプト

set -e

echo "🧪 Running tests with coverage..."
uv run pytest --cov=src --cov-report=html --cov-report=term --cov-report=json -v

echo ""
echo "📊 Coverage Summary:"
echo "===================="

# JSONレポートから総カバレッジを抽出
if [ -f coverage.json ]; then
    COVERAGE=$(python3 -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")")
    echo "Total Coverage: ${COVERAGE}%"

    # バッジの色を決定
    if (( $(echo "$COVERAGE >= 90" | bc -l) )); then
        COLOR="brightgreen"
    elif (( $(echo "$COVERAGE >= 80" | bc -l) )); then
        COLOR="green"
    elif (( $(echo "$COVERAGE >= 70" | bc -l) )); then
        COLOR="yellow"
    else
        COLOR="red"
    fi

    echo "Badge Color: ${COLOR}"
    echo ""
    echo "📝 Update README.md badge with:"
    echo "![Coverage](https://img.shields.io/badge/coverage-${COVERAGE}%25-${COLOR})"
else
    echo "⚠️  coverage.json not found"
fi

echo ""
echo "✅ Coverage report generated!"
echo "📂 HTML report: htmlcov/index.html"
echo ""
echo "To view the report:"
echo "  macOS:  open htmlcov/index.html"
echo "  Linux:  xdg-open htmlcov/index.html"
echo "  Windows: start htmlcov/index.html"
