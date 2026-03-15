#!/bin/bash
# Soft-fail check: warn if any Python/TypeScript file exceeds 500 lines
MAX=500
FOUND=0
for f in $(find backend/app frontend/src -name "*.py" -o -name "*.tsx" -o -name "*.ts" | grep -v node_modules | grep -v __pycache__ | grep -v ".test." | grep -v ".d.ts"); do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt "$MAX" ]; then
    echo "WARNING: $f has $lines lines (max $MAX)"
    FOUND=1
  fi
done
if [ "$FOUND" -eq 1 ]; then
  echo "::warning::Some files exceed the $MAX-line limit. Consider splitting."
fi
exit 0  # soft-fail: don't block CI
