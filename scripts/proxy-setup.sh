#!/usr/bin/env bash
# Setup mitmproxy for capturing HelloTalk traffic
#
# Prerequisites:
#   - mitmproxy installed (pip install mitmproxy)
#   - Android device/emulator on same network
#
# Usage:
#   bash scripts/proxy-setup.sh [port]

set -euo pipefail

PORT="${1:-8080}"
CAPTURE_DIR="captures"

mkdir -p "$CAPTURE_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CAPTURE_FILE="$CAPTURE_DIR/hellotalk_${TIMESTAMP}.mitm"

echo "=== HelloTalk Traffic Capture ==="
echo ""
echo "1. Set your device's Wi-Fi proxy to this machine's IP, port $PORT"
echo "2. On the device, visit http://mitm.it to install the CA certificate"
echo "3. Open HelloTalk and use the app normally"
echo "4. Traffic will be saved to: $CAPTURE_FILE"
echo ""
echo "Starting mitmproxy on port $PORT..."
echo "Press Ctrl+C to stop."
echo ""

mitmdump \
  --listen-port "$PORT" \
  --save-stream-file "$CAPTURE_FILE" \
  --set flow_detail=2 \
  --showhost \
  -k
