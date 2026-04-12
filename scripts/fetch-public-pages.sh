#!/bin/bash
#
# Fetch public HelloTalk marketing and careers pages.
#
# Runs from a GitHub Actions runner. The Claude Code sandbox cannot reach
# hellotalk.com (egress allowlist blocks it), but GitHub runners can.
#
# Saves raw HTML + extracted text to docs/research/ so Claude can read
# them back from the repo. These pages often reveal internal tech stack,
# team names, service names, and hiring priorities that help reverse-
# engineer how the product is built behind the scenes.

set -uo pipefail

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
OUT="docs/research"
mkdir -p "$OUT"

fetch() {
  local name="$1"
  local url="$2"
  local out_html="$OUT/${name}.html"
  local out_meta="$OUT/${name}.meta"

  echo "  fetching $url"
  local code size
  code_and_size=$(curl -sS -m 30 -L \
    -A "$UA" \
    -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
    -H "Accept-Language: en-US,en;q=0.9" \
    -o "$out_html" \
    -w "%{http_code}|%{size_download}" \
    "$url" 2>&1 || echo "000|0")

  code="${code_and_size%%|*}"
  size="${code_and_size##*|}"
  {
    echo "name=$name"
    echo "url=$url"
    echo "http_code=$code"
    echo "size=$size"
    echo "fetched_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$out_meta"
  echo "    -> $code  $size bytes  -> $out_html"
}

echo "== HelloTalk public page fetch =="
echo ""

# The page the user specifically asked us to look at
fetch "hellotalk-jobs" "https://www.hellotalk.com/jobs"

# Root page — may reveal tech stack via script tags, meta, etc.
fetch "hellotalk-root" "https://www.hellotalk.com/"

# Content policy — referenced in our escalation materials, useful to have
# the current version on file
fetch "hellotalk-content-policy" "https://www.hellotalk.com/content-policy"

# Privacy policy — sometimes enumerates the data pipeline / backends
fetch "hellotalk-privacy" "https://www.hellotalk.com/privacy"

# Terms of service
fetch "hellotalk-tos" "https://www.hellotalk.com/terms"

# FAQ / help — may mention internal error codes and support flows
fetch "hellotalk-help" "https://www.hellotalk.com/help"

# Careers subpath variations (some CMS setups put the content here instead)
fetch "hellotalk-careers" "https://www.hellotalk.com/careers"
fetch "hellotalk-about" "https://www.hellotalk.com/about"

# Web client — the JS bundles sometimes leak endpoint paths and field names
fetch "hellotalk-web-root" "https://web.hellotalk.com/"
fetch "hellotalk-web-login" "https://web.hellotalk.com/login"
fetch "hellotalk-web-chat" "https://web.hellotalk.com/chat"

# Static asset manifests — if the web app is a SPA, these may list all
# JS/CSS bundles which we can grep for API paths
fetch "hellotalk-web-manifest" "https://web.hellotalk.com/asset-manifest.json"
fetch "hellotalk-web-manifest-alt" "https://web.hellotalk.com/manifest.json"

# Extract <script src="..."> paths from the web client root and queue
# them for a follow-up fetch. This gives us the JS bundle URLs even
# if the asset manifest isn't exposed.
if [[ -s "$OUT/hellotalk-web-root.html" ]]; then
  echo ""
  echo "  extracting script src paths from web-root.html..."
  grep -oE '<script[^>]+src="[^"]+"' "$OUT/hellotalk-web-root.html" 2>/dev/null \
    | grep -oE 'src="[^"]+"' \
    | sed 's/src="//; s/"$//' \
    | sort -u > "$OUT/web-root-scripts.txt"
  script_count=$(wc -l < "$OUT/web-root-scripts.txt" 2>/dev/null || echo 0)
  echo "    found $script_count script src paths -> $OUT/web-root-scripts.txt"

  # Fetch the first 10 JS bundles so we can grep them for API paths
  count=0
  while IFS= read -r src; do
    [[ -z "$src" ]] && continue
    count=$((count+1))
    [[ $count -gt 10 ]] && break

    # Resolve relative URLs against web.hellotalk.com
    case "$src" in
      http*) full_url="$src" ;;
      //*) full_url="https:$src" ;;
      /*) full_url="https://web.hellotalk.com$src" ;;
      *) full_url="https://web.hellotalk.com/$src" ;;
    esac

    name="web-bundle-$count"
    fetch "$name" "$full_url"
  done < "$OUT/web-root-scripts.txt"

  # Grep the downloaded bundles for anything that looks like an API path
  echo ""
  echo "  grepping bundles for API paths..."
  {
    echo "# API-like strings extracted from web.hellotalk.com JS bundles"
    echo "# Extracted $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    for f in "$OUT"/web-bundle-*.html; do
      [[ -f "$f" ]] || continue
      echo ""
      echo "## From $(basename "$f")"
      grep -hoE '"/[a-zA-Z0-9_/]+(/[a-zA-Z0-9_/]+)+"' "$f" 2>/dev/null | sort -u | head -100 || true
      grep -hoE '"/v[0-9]+/[a-zA-Z0-9_/]+"' "$f" 2>/dev/null | sort -u | head -100 || true
      grep -hoE '"/go_[a-zA-Z_]+/v[0-9]+/[a-zA-Z0-9_/]+"' "$f" 2>/dev/null | sort -u | head -100 || true
    done
  } > "$OUT/web-bundle-api-paths.txt"
fi

echo ""
echo "== Done =="
ls -la "$OUT"
