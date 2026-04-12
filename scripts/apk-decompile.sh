#!/bin/bash
#
# Download the HelloTalk APK and extract all Retrofit API endpoint
# definitions using JADX. Runs from a GitHub Actions runner so the
# decompiled output can be committed back into the repo for reference.
#
# This is a one-shot intelligence-gathering step, not a monitor. Don't
# run it on a schedule — it's big (APK is ~300 MB, decompile takes
# 10-20 minutes on a 2-core runner).
#
# Outputs:
#   docs/research/apk-version.txt      — which APK version was processed
#   docs/research/apk-endpoints.txt    — grep of all Retrofit HTTP
#                                         annotations extracted
#   docs/research/apk-urls.txt         — all hardcoded URL strings
#   docs/research/apk-tree.txt         — top-level package structure

set -uo pipefail

OUT="docs/research"
mkdir -p "$OUT"

APK_URL="https://d.apkpure.com/b/XAPK/com.hellotalk?version=latest"
# Fallback direct URLs if apkpure changes
APK_URL_2="https://apps.evozi.com/apk-downloader/download/com.hellotalk/"

WORKDIR="$(mktemp -d)"
APK_PATH="$WORKDIR/hellotalk.apk"
DECOMPILE_DIR="$WORKDIR/jadx-out"

echo "== HelloTalk APK decompile =="
echo "  workdir: $WORKDIR"
echo ""

# --- Install JADX -----------------------------------------------------------
if ! command -v jadx &>/dev/null; then
  echo "  installing jadx..."
  sudo apt-get update -qq >/dev/null 2>&1 || true
  sudo apt-get install -y jadx -qq >/dev/null 2>&1 || {
    # Fallback: download the release JAR
    JADX_VERSION="1.5.0"
    JADX_URL="https://github.com/skylot/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip"
    echo "    apt install failed, downloading jadx release..."
    curl -sSL -o "$WORKDIR/jadx.zip" "$JADX_URL"
    unzip -q "$WORKDIR/jadx.zip" -d "$WORKDIR/jadx"
    JADX_BIN="$WORKDIR/jadx/bin/jadx"
    chmod +x "$JADX_BIN"
    alias jadx="$JADX_BIN"
  }
fi

# --- Download the APK -------------------------------------------------------
echo "  downloading APK..."
curl -sSL -A "Mozilla/5.0" -o "$APK_PATH" "$APK_URL" || {
  echo "    first source failed, trying fallback..."
  curl -sSL -A "Mozilla/5.0" -o "$APK_PATH" "$APK_URL_2"
}

APK_SIZE=$(stat -c%s "$APK_PATH" 2>/dev/null || stat -f%z "$APK_PATH" 2>/dev/null)
echo "    downloaded: $APK_SIZE bytes"

if [[ "$APK_SIZE" -lt 1000000 ]]; then
  echo "  APK download looks too small — writing stub and exiting"
  {
    echo "APK download failed"
    echo "url1=$APK_URL"
    echo "url2=$APK_URL_2"
    echo "size=$APK_SIZE"
    echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$OUT/apk-download-failed.txt"
  exit 0
fi

# --- Decompile with JADX ----------------------------------------------------
echo "  running jadx..."
JADX_CMD="${JADX_BIN:-jadx}"
timeout 1800 "$JADX_CMD" --no-res --no-imports -d "$DECOMPILE_DIR" "$APK_PATH" 2>&1 | tail -20 || {
  echo "    jadx timeout or error — will try to work with partial output"
}

# --- Extract Retrofit endpoints --------------------------------------------
echo "  extracting Retrofit endpoints..."
{
  echo "# Retrofit API endpoint annotations"
  echo "# Extracted $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  find "$DECOMPILE_DIR" -name '*.java' -print0 2>/dev/null \
    | xargs -0 grep -hEn '@(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(' 2>/dev/null \
    | sort -u
} > "$OUT/apk-endpoints.txt"

endpoint_count=$(grep -cE '@(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)' "$OUT/apk-endpoints.txt" 2>/dev/null || echo 0)
echo "    found $endpoint_count endpoint annotations"

# --- Extract hardcoded URLs -------------------------------------------------
echo "  extracting URL strings..."
{
  echo "# Hardcoded URL strings"
  echo "# Extracted $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  find "$DECOMPILE_DIR" -name '*.java' -print0 2>/dev/null \
    | xargs -0 grep -hoE '"/[a-zA-Z0-9_/]+"' 2>/dev/null \
    | sort -u \
    | head -500
} > "$OUT/apk-urls.txt"

# --- Package tree (top-level overview) --------------------------------------
echo "  writing package tree..."
{
  echo "# Top-level package tree"
  find "$DECOMPILE_DIR" -type d 2>/dev/null | head -100
} > "$OUT/apk-tree.txt"

# --- Version info -----------------------------------------------------------
{
  echo "APK path: $APK_PATH"
  echo "APK size: $APK_SIZE bytes"
  echo "Downloaded: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Decompile dir: $DECOMPILE_DIR"
  echo "Endpoint count: $endpoint_count"
} > "$OUT/apk-version.txt"

echo ""
echo "== APK decompile done =="
ls -la "$OUT"/apk-*.txt 2>/dev/null
