/**
 * Proxyman Scripting — Strip HelloTalk Encryption Headers
 *
 * PURPOSE: Forces HelloTalk's API to respond with plain JSON instead of
 * encrypted ht/encbin payloads by removing the encryption negotiation headers.
 *
 * HOW TO USE (on your Mac with Proxyman):
 * 1. Open Proxyman on Mac
 * 2. Make sure your iPhone is routing traffic through Mac's Proxyman
 *    (iPhone WiFi settings → HTTP Proxy → Manual → your Mac's IP, port 9090)
 * 3. In Proxyman: Tools → Scripting → Create New Script
 * 4. Set the matching rule to: *hellotalk8.com*
 * 5. Paste this entire script
 * 6. Enable it and use HelloTalk on your phone
 * 7. Watch — if responses come back as JSON instead of encrypted blobs, IT WORKED
 *
 * WHAT THIS DOES:
 * - Removes the x-ht-pub header (client's ECDH public key)
 * - Changes Content-Type from ht/encbin to application/json
 * - This MIGHT cause the server to fall back to unencrypted JSON responses
 * - If the server requires encryption, requests will fail (just disable the script)
 */

async function onRequest(context, url, request) {
    // Only modify HelloTalk API requests
    if (!url.includes("hellotalk8.com")) {
        return request;
    }

    // Remove the encryption public key header
    if (request.headers["x-ht-pub"]) {
        console.log("[HT-STRIP] Removing x-ht-pub from: " + url);
        delete request.headers["x-ht-pub"];
    }
    if (request.headers["X-Ht-Pub"]) {
        delete request.headers["X-Ht-Pub"];
    }

    // Change encrypted content type to plain JSON
    if (request.headers["Content-Type"] === "ht/encbin") {
        console.log("[HT-STRIP] Changing Content-Type to JSON for: " + url);
        request.headers["Content-Type"] = "application/json";
    }
    if (request.headers["content-type"] === "ht/encbin") {
        request.headers["content-type"] = "application/json";
    }

    // Log the modified request
    console.log("[HT-STRIP] " + request.method + " " + url);

    return request;
}

async function onResponse(context, url, request, response) {
    // Only log HelloTalk API responses
    if (!url.includes("hellotalk8.com")) {
        return response;
    }

    var ct = response.headers["content-type"] || response.headers["Content-Type"] || "";
    var status = response.statusCode;

    if (ct.includes("json")) {
        // SUCCESS — we got plain JSON back!
        console.log("[HT-STRIP] ✅ JSON response from: " + url + " (status " + status + ")");

        // Try to parse and log interesting fields
        try {
            var body = JSON.parse(response.body);
            var bodyStr = JSON.stringify(body);

            // Check for visibility/trust related fields
            var keywords = ["trust", "score", "rank", "weight", "restrict",
                          "ban", "flag", "visible", "shadow", "penalty",
                          "boost", "recommend", "exposure", "level", "vip"];

            for (var i = 0; i < keywords.length; i++) {
                if (bodyStr.toLowerCase().includes(keywords[i])) {
                    console.log("[HT-STRIP] ⚠️ INTERESTING FIELD '" + keywords[i] + "' found in: " + url);
                }
            }
        } catch (e) {
            // Not parseable, that's ok
        }
    } else if (ct.includes("encbin")) {
        // Still encrypted — the fallback didn't work for this endpoint
        console.log("[HT-STRIP] ❌ Still encrypted: " + url + " (status " + status + ")");
    } else {
        console.log("[HT-STRIP] Response: " + url + " → " + ct + " (status " + status + ")");
    }

    return response;
}
