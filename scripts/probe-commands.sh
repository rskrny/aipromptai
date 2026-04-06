#!/bin/bash
#
# HelloTalk API Probe Commands
#
# Run these from ANY computer/device that can reach the internet.
# Each command tests a different endpoint WITHOUT encryption headers.
#
# OR: Use Proxyman iOS "Compose" feature — paste the URL, method,
# headers, and body for each probe.
#
# YOUR AUTH TOKEN (from Proxyman capture):
TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzgwMzA1NzAsInNyYyI6MiwidWlkIjo5ODc1NTE1MH0.Og3Hb2l95RB7SPuw5TRR5Q_rJsnSb1ClqMaCP-Abqh8"
UID="98755150"
DID="29ea6362a590de52972d100cd01ab78dd7b7b6c9"
BASE="https://api-global.hellotalk8.com"

# Common headers for all requests
HEADERS="-H 'Authorization: $TOKEN' \
  -H 'x-ht-uid: $UID' \
  -H 'x-ht-did: $DID' \
  -H 'x-ht-os: ios' \
  -H 'x-ht-timezone: -10.00' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'User-Agent: ios;6.3.0;iPhone14,3;26.4;98755150' \
  -H 'Accept-Language: en-US;q=1.0'"

echo "============================================"
echo "  HelloTalk API Probe"
echo "  NO encryption headers (testing fallback)"
echo "============================================"
echo ""

# ---------------------------------------------------
# PROBE 1: Boost Status (KNOWN WORKING endpoint)
# ---------------------------------------------------
echo "--- PROBE 1: Boost Status ---"
eval curl -s -X POST "$BASE/virtual_product/v1/virtual_product/free_recommend_status" \
  $HEADERS \
  -d '{"os_version":"26.4","nationality":"US","lang_id":1,"native_lang":1,"os_type":0,"user_id":98755150,"app_version":"6.3.0","virtual_type":14}' | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 2: Trigger a Boost
# ---------------------------------------------------
echo "--- PROBE 2: Trigger Boost ---"
eval curl -s -X POST "$BASE/virtual_product/v1/recommend/post_recommend_btn" \
  $HEADERS \
  -d '{"os_version":"26.4","nationality":"US","lang_id":1,"native_lang":1,"os_type":0,"user_id":98755150,"app_version":"6.3.0"}' | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 3: Language Info (KNOWN WORKING)
# ---------------------------------------------------
echo "--- PROBE 3: Language Info ---"
eval curl -s -X GET "$BASE/go_user_search/v1/go_user_info/get_user_langs?user_id=98755150" \
  $HEADERS | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 4: User Info from Search Service
# ---------------------------------------------------
echo "--- PROBE 4: User Info (search service) ---"
eval curl -s -X GET "$BASE/go_user_search/v1/go_user_info/get_user_info?user_id=98755150" \
  $HEADERS | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 5: User Detail from Search Service
# ---------------------------------------------------
echo "--- PROBE 5: User Detail ---"
eval curl -s -X GET "$BASE/go_user_search/v1/go_user_info/get_user_detail?user_id=98755150" \
  $HEADERS | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 6: Exposure Record (visibility metrics)
# ---------------------------------------------------
echo "--- PROBE 6: Exposure Record ---"
eval curl -s -X POST "$BASE/v2/moment/query_expose_record" \
  $HEADERS \
  -d '{"user_id":98755150}' | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 7: Moments Latest
# ---------------------------------------------------
echo "--- PROBE 7: Latest Moments ---"
eval curl -s -X POST "$BASE/v2/moment/latest" \
  $HEADERS \
  -d '{"user_id":98755150,"page":1,"count":5}' | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 8: Nearby Count
# ---------------------------------------------------
echo "--- PROBE 8: Nearby Count ---"
eval curl -s -X GET "$BASE/go_user_search/v2/nearby_count?latitude=20.7564&longitude=-155.9900&learnlang=2&page=1&sort=distance&userid=98755150" \
  $HEADERS | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 9: Moment Tab Info
# ---------------------------------------------------
echo "--- PROBE 9: Moment Tab Info ---"
eval curl -s -X POST "$BASE/go_moment/v2/get_moment_tab_info" \
  $HEADERS \
  -d '{"user_id":98755150}' | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

# ---------------------------------------------------
# PROBE 10: Translation Config
# ---------------------------------------------------
echo "--- PROBE 10: Translation Config ---"
eval curl -s -X POST "$BASE/translate/v1/config" \
  $HEADERS \
  -d '{}' | python3 -m json.tool 2>/dev/null || echo "(not JSON)"
echo ""

echo "============================================"
echo "  DONE — copy all output and paste it back"
echo "============================================"
