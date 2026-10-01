#!/usr/bin/env bash
# Capture a REAL screen from the booted iOS Simulator with a clean status bar (9:41, full battery).
# Usage: ./capture/ios_simulator.sh screens/01.png
# Tip: use an iPhone 16 Pro Max / 15 Pro Max simulator → 1320x2868 or 1290x2796 captures.
# The captured screen already has a status bar → set "status_bar": "none" for this phone in panorama.json.
set -euo pipefail
OUT="${1:?output path, e.g. screens/01.png}"
mkdir -p "$(dirname "$OUT")"
xcrun simctl status_bar booted override --time "9:41" --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 --wifiBars 3 --dataNetwork wifi
sleep 1
xcrun simctl io booted screenshot "$OUT"
echo "✓ $OUT"
