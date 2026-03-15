#!/bin/bash
# Check for except Exception without logging on the next line
FOUND=0
while IFS= read -r file; do
  grep -n "except Exception:" "$file" | while read -r line; do
    lineno=$(echo "$line" | cut -d: -f1)
    next=$((lineno + 1))
    nextline=$(sed -n "${next}p" "$file")
    if ! echo "$nextline" | grep -qE "logger\.(exception|warning|error|info)|raise|pass.*#.*intentional"; then
      echo "WARNING: $file:$lineno — except Exception without logging"
      FOUND=1
    fi
  done
done < <(find backend/app -name "*.py" ! -path "*__pycache__*")
exit 0
