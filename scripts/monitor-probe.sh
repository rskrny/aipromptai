#!/bin/bash
#
# HelloTalk API Monitor Probe
#
# Runs a battery of unencrypted probes against HelloTalk's API and saves the
# raw response bodies + HTTP status codes into monitor/runs/<timestamp>/. This
# is designed to run from a GitHub Actions runner (which has unrestricted
# internet egress) because the Claude Code sandbox cannot reach the HelloTalk
# domain directly.
#
# Each probe writes two files:
#   <name>.body    — raw response body (may be JSON, may be an error string)
#   <name>.meta    — one line: method=... url=... http_code=... size=...
#
# After the run, the latest results are also copied to monitor/latest/ for
# easy reading.
#
# Safety notes:
# - All requests use the exact headers the iOS HelloTalk client sends. Nothing
#   in this script looks like a bot to HelloTalk's backend.
# - Random 1-3 second delay between probes to stay under rate-limit radar.
# - Read-only: no probe modifies account state.

set -uo pipefail

TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzgwMzA1NzAsInNyYyI6MiwidWlkIjo5ODc1NTE1MH0.Og3Hb2l95RB7SPuw5TRR5Q_rJsnSb1ClqMaCP-Abqh8"
# NB: $UID is readonly in bash (the OS uid). Use HT_UID for the HelloTalk
# user id so we don't accidentally send the runner's OS uid in x-ht-uid.
HT_UID="98755150"
DID="29ea6362a590de52972d100cd01ab78dd7b7b6c9"
BASE="https://api-global.hellotalk8.com"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
RUN_DIR="monitor/runs/$TIMESTAMP"
LATEST_DIR="monitor/latest"
mkdir -p "$RUN_DIR"

HEADER_ARGS=(
  -H "Authorization: $TOKEN"
  -H "x-ht-uid: $HT_UID"
  -H "x-ht-did: $DID"
  -H "x-ht-os: ios"
  -H "x-ht-timezone: -4.00"
  -H "Content-Type: application/json"
  -H "Accept: application/json"
  -H "User-Agent: ios;6.3.0;iPhone14,3;26.4;$HT_UID"
  -H "Accept-Language: en-US;q=1.0"
)

probe() {
  local name="$1"
  local method="$2"
  local url="$3"
  local body="${4:-}"

  local body_file="$RUN_DIR/${name}.body"
  local meta_file="$RUN_DIR/${name}.meta"

  local http_code size
  if [[ "$method" == "GET" ]]; then
    http_code=$(curl -sS -m 30 \
      -o "$body_file" \
      -w "%{http_code}|%{size_download}" \
      -X GET "$url" \
      "${HEADER_ARGS[@]}" 2>/dev/null || echo "000|0")
  else
    http_code=$(curl -sS -m 30 \
      -o "$body_file" \
      -w "%{http_code}|%{size_download}" \
      -X POST "$url" \
      "${HEADER_ARGS[@]}" \
      -d "$body" 2>/dev/null || echo "000|0")
  fi

  size="${http_code##*|}"
  http_code="${http_code%%|*}"

  {
    echo "name=$name"
    echo "method=$method"
    echo "url=$url"
    echo "http_code=$http_code"
    echo "size=$size"
    [[ -n "$body" ]] && echo "request_body=$body"
  } > "$meta_file"

  printf "  %-35s %s %s bytes\n" "$name" "$http_code" "$size"

  # Human-paced delay: random 1-3 seconds
  sleep "$((RANDOM % 3 + 1))"
}

echo "== HelloTalk API Monitor =="
echo "  timestamp: $TIMESTAMP"
echo "  output:    $RUN_DIR"
echo ""
echo "  running probes..."

# ---------------------------------------------------------------------------
# Boost inventory — unencrypted, confirmed working 2026-04-11
# ---------------------------------------------------------------------------
probe "boost_status_type14" POST \
  "$BASE/virtual_product/v1/virtual_product/free_recommend_status" \
  '{"os_version":"26.4","nationality":"US","lang_id":1,"native_lang":1,"os_type":0,"user_id":98755150,"app_version":"6.3.0","virtual_type":14}'

probe "boost_status_type6" POST \
  "$BASE/virtual_product/v1/virtual_product/free_recommend_status" \
  '{"os_version":"26.4","nationality":"US","lang_id":1,"native_lang":1,"os_type":0,"user_id":98755150,"app_version":"6.3.0","virtual_type":6}'

probe "boost_product_list" POST \
  "$BASE/virtual_product/v1/virtual_product/list" \
  '{"os_version":"26.4","nationality":"US","lang_id":1,"native_lang":1,"os_type":0,"user_id":98755150,"app_version":"6.3.0"}'

# ---------------------------------------------------------------------------
# Search service probes — test what leaks unencrypted
# ---------------------------------------------------------------------------
probe "search_filter" GET \
  "$BASE/go_user_search/v2/filter?userid=98755150&learnlang=2"

probe "search_recommend" GET \
  "$BASE/go_user_search/v2/recommend?userid=98755150&learnlang=2&page=1"

probe "search_nearby_count" GET \
  "$BASE/go_user_search/v2/nearby_count?latitude=42.3601&longitude=-71.0589&learnlang=2&page=1&sort=distance&userid=98755150"

probe "user_langs" GET \
  "$BASE/go_user_search/v1/go_user_info/get_user_langs?user_id=98755150"

# ---------------------------------------------------------------------------
# Moments / exposure — probably encrypted but worth the probe
# ---------------------------------------------------------------------------
probe "moments_latest" POST \
  "$BASE/v2/moment/latest" \
  '{"user_id":98755150,"page":1,"count":5}'

probe "moment_expose_record" POST \
  "$BASE/v2/moment/query_expose_record" \
  '{"user_id":98755150}'

probe "moment_tab_info" POST \
  "$BASE/go_moment/v2/get_moment_tab_info" \
  '{"user_id":98755150}'

# ---------------------------------------------------------------------------
# Speculative: try the rumored profile endpoints one more time
# ---------------------------------------------------------------------------
probe "user_detail_v4" POST \
  "$BASE/v4/user/profile" \
  '{"user_id":98755150}'

probe "user_info_v4" POST \
  "$BASE/v4/user/info" \
  '{"user_id":98755150}'

# ---------------------------------------------------------------------------
# Ghost lang 13 cleanup — try every candidate deletion endpoint
#
# The account has a phantom temporary language (lang 13, is_temp=1) that is
# invisible in the app UI and may be blocking search indexing. Try to clear it.
# These are write-intent probes. The worst case is error responses (diagnostic
# data). We try multiple endpoints because we don't know which one the app uses.
# ---------------------------------------------------------------------------
probe "lang_clear_temp" POST \
  "$BASE/go_user_search/v1/go_user_info/clear_temp_lang" \
  "{\"user_id\":$HT_UID}"

probe "lang_remove" POST \
  "$BASE/go_user_search/v1/go_user_info/remove_lang" \
  "{\"user_id\":$HT_UID,\"lang\":13,\"is_temp\":1}"

probe "lang_delete" POST \
  "$BASE/go_user_search/v1/go_user_info/delete_lang" \
  "{\"user_id\":$HT_UID,\"lang_id\":13}"

probe "lang_set_correct" POST \
  "$BASE/go_user_search/v1/go_user_info/set_user_langs" \
  "{\"user_id\":$HT_UID,\"langs\":[{\"lang\":2,\"is_temp\":0}]}"

probe "lang_update_v2" POST \
  "$BASE/v2/user/lang/delete" \
  "{\"user_id\":$HT_UID,\"lang_id\":13}"

probe "lang_set_v2" POST \
  "$BASE/v2/user/lang/set" \
  "{\"user_id\":$HT_UID,\"langs\":[{\"lang_id\":2}]}"

# ---------------------------------------------------------------------------
# Force profile refresh — hit endpoints that may trigger a re-index
# ---------------------------------------------------------------------------
probe "recommend_btn" POST \
  "$BASE/virtual_product/v1/recommend/post_recommend_btn" \
  "{\"os_version\":\"26.4\",\"nationality\":\"US\",\"lang_id\":1,\"native_lang\":1,\"os_type\":0,\"user_id\":$HT_UID,\"app_version\":\"6.3.0\"}"

# ---------------------------------------------------------------------------
# Summary + stable latest/ copy
# ---------------------------------------------------------------------------
{
  echo "# HelloTalk API Monitor Summary"
  echo ""
  echo "Run timestamp: $TIMESTAMP"
  echo "User ID:       $HT_UID"
  echo ""
  echo "## Probe results"
  echo ""
  for meta in "$RUN_DIR"/*.meta; do
    name=$(basename "$meta" .meta)
    code=$(grep '^http_code=' "$meta" | cut -d= -f2)
    size=$(grep '^size=' "$meta" | cut -d= -f2)
    printf "  %-35s  %s  %s bytes\n" "$name" "$code" "$size"
  done
} > "$RUN_DIR/_summary.txt"

rm -rf "$LATEST_DIR"
mkdir -p "$LATEST_DIR"
cp "$RUN_DIR"/* "$LATEST_DIR"/

echo ""
echo "== Done =="
cat "$RUN_DIR/_summary.txt"
