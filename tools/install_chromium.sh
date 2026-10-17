#!/usr/bin/env bash
# Install a locally signed xpChromium test APK and its startup configuration.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 /path/to/Chromium.apk [/path/to/fingerprint.json]" >&2
  echo "Set ANDROID_SERIAL to select a device. Omit JSON to keep its current file." >&2
  exit 2
fi

apk=$1
config=${2:-}
package=org.chromium.chrome
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
[[ -f "$apk" ]] || { echo "APK not found: $apk" >&2; exit 2; }
[[ -z "$config" || -f "$config" ]] || { echo "Configuration not found: $config" >&2; exit 2; }
adb_tool=${ADB:-}
if [[ -z "$adb_tool" ]]; then
  adb_tool=$(command -v adb || true)
fi
if [[ -z "$adb_tool" ]]; then
  for candidate in "${ANDROID_SDK_ROOT:-}/platform-tools/adb" \
    "${ANDROID_HOME:-}/platform-tools/adb" \
    "$HOME/Library/Android/sdk/platform-tools/adb" "$HOME/Android/Sdk/platform-tools/adb"; do
    if [[ -x "$candidate" ]]; then adb_tool=$candidate; break; fi
  done
fi
[[ -n "$adb_tool" && -x "$adb_tool" ]] || { echo "Set ADB to the Android adb executable." >&2; exit 2; }
run_adb() { "$adb_tool" "$@"; }

run_adb get-state >/dev/null
sdk=$(run_adb shell getprop ro.build.version.sdk | tr -d '\r')
[[ "$sdk" =~ ^[0-9]+$ && "$sdk" -ge 29 ]] || { echo "Android 10+ required." >&2; exit 1; }
abis=$(run_adb shell getprop ro.product.cpu.abilist | tr -d '\r')
[[ "$abis" == *arm64-v8a* ]] || { echo "An arm64 Android device is required." >&2; exit 1; }

run_adb install -r "$apk"
run_adb shell am force-stop "$package"
if (( sdk >= 30 )); then
  run_adb shell appops set "$package" MANAGE_EXTERNAL_STORAGE allow
else
  run_adb shell pm grant "$package" android.permission.READ_EXTERNAL_STORAGE
fi
run_adb shell mkdir -p /sdcard/xpChromium
if [[ -n "$config" ]]; then
  run_adb push "$config" /sdcard/xpChromium/fingerprint.json
fi
run_adb push "$repo/tests/identity-smoke.html" /sdcard/xpChromium/identity-smoke.html
run_adb shell monkey -p "$package" -c android.intent.category.LAUNCHER 1 >/dev/null
echo "Installed. Finish Chromium's first-run screen, then open:"
echo "file:///sdcard/xpChromium/identity-smoke.html?language=zh-CN&timezone=Asia%2FShanghai&noise=1"
echo "Those expectations match fingerprint.browser.json; adjust them for other profiles."
echo "After editing fingerprint.json, force-stop Chromium and launch it again."
