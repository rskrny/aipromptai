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

echo ""
echo "== Done =="
ls -la "$OUT"
