#!/usr/bin/env bash
# Capture a REAL screen from a connected Android device/emulator in System UI demo mode.
# Usage: ./capture/android_emulator.sh screens/01.png
set -euo pipefail
OUT="${1:?output path, e.g. screens/01.png}"
mkdir -p "$(dirname "$OUT")"
adb shell settings put global sysui_demo_allowed 1
adb shell am broadcast -a com.android.systemui.demo -e command enter >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0941 >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command network -e wifi show -e level 4 >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command notifications -e visible false >/dev/null
sleep 1
adb exec-out screencap -p > "$OUT"
adb shell am broadcast -a com.android.systemui.demo -e command exit >/dev/null
echo "✓ $OUT"
