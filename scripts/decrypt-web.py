#!/usr/bin/env python3
"""
Decrypt HelloTalk web IM traffic using XTEA.

Connects to Chrome, intercepts the ht-enc responses, and decrypts them
using the session UUID as the XTEA key.
"""
import asyncio
import json
import struct
from playwright.async_api import async_playwright


def xtea_decrypt_block(block, key, rounds=32):
    """Decrypt a single 8-byte XTEA block."""
    v0, v1 = struct.unpack(">II", block)
    k = struct.unpack(">4I", key)
    delta = 0x9E3779B9
    total = (delta * rounds) & 0xFFFFFFFF

    for _ in range(rounds):
        v1 = (v1 - (((v0 << 4 ^ v0 >> 5) + v0) ^ (total + k[(total >> 11) & 3]))) & 0xFFFFFFFF
        total = (total - delta) & 0xFFFFFFFF
        v0 = (v0 - (((v1 << 4 ^ v1 >> 5) + v1) ^ (total + k[total & 3]))) & 0xFFFFFFFF

    return struct.pack(">II", v0, v1)


def xtea_decrypt(data, key_bytes):
    """Decrypt data using XTEA in CBC mode (or ECB)."""
    if len(data) % 8 != 0:
        # Pad to 8-byte boundary
        data = data + b'\x00' * (8 - len(data) % 8)

    result = b''
    prev = b'\x00' * 8  # CBC IV

    # Try ECB first
    ecb_result = b''
    for i in range(0, len(data), 8):
        block = data[i:i+8]
        decrypted = xtea_decrypt_block(block, key_bytes)
        ecb_result += decrypted

    # Try CBC
    cbc_result = b''
    prev = b'\x00' * 8
    for i in range(0, len(data), 8):
        block = data[i:i+8]
        decrypted = xtea_decrypt_block(block, key_bytes)
        plaintext = bytes(a ^ b for a, b in zip(decrypted, prev))
        cbc_result += plaintext
        prev = block

    return ecb_result, cbc_result


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"Connected: {page.url}")

    session_uuid = None
    decrypted_messages = []

    async def on_response(response):
        nonlocal session_uuid
        url = response.url
        ct = response.headers.get("content-type", "")

        # Capture the session UUID from sync URLs
        if "hellotalk8.com/im/lg/sync" in url:
            parts = url.split("/")
            for i, p in enumerate(parts):
                if p == "sync" or p == "sync_to_web":
                    if i + 1 < len(parts):
                        uuid_candidate = parts[i + 1]
                        if len(uuid_candidate) == 36 and "-" in uuid_candidate:
                            session_uuid = uuid_candidate
                            print(f"  Session UUID: {session_uuid}")

        # Decrypt ht-enc responses
        if "ht-enc" in ct and session_uuid:
            try:
                body = await response.body()
                key_hex = session_uuid.replace("-", "")
                key_bytes = bytes.fromhex(key_hex)

                print(f"\n  Encrypted response: {len(body)}b from {url.split('?')[0]}")
                print(f"  Using key: {key_hex}")
                print(f"  First 32 bytes hex: {body[:32].hex()}")

                ecb_result, cbc_result = xtea_decrypt(body, key_bytes)

                # Check which one looks like valid data
                for label, result in [("ECB", ecb_result), ("CBC", cbc_result)]:
                    # Try to decode as UTF-8
                    try:
                        text = result.decode("utf-8", errors="strict")
                        if text.isprintable() or "{" in text[:100]:
                            print(f"\n  *** {label} DECRYPTION SUCCESS ***")
                            print(f"  {text[:500]}")
                            decrypted_messages.append({
                                "url": url,
                                "mode": label,
                                "text": text[:2000],
                            })
                            break
                    except UnicodeDecodeError:
                        pass

                    # Try to find JSON in the result
                    try:
                        # Look for JSON start
                        for offset in range(min(32, len(result))):
                            chunk = result[offset:]
                            text = chunk.decode("utf-8", errors="ignore")
                            json_start = text.find("{")
                            if json_start >= 0 and json_start < 50:
                                json_text = text[json_start:]
                                try:
                                    parsed = json.loads(json_text)
                                    print(f"\n  *** {label} DECRYPTION SUCCESS (offset {offset + json_start}) ***")
                                    print(f"  {json.dumps(parsed, ensure_ascii=False)[:500]}")
                                    decrypted_messages.append({
                                        "url": url,
                                        "mode": label,
                                        "offset": offset + json_start,
                                        "json": parsed,
                                    })
                                    break
                                except json.JSONDecodeError:
                                    continue
                    except Exception:
                        pass
                else:
                    # Neither worked cleanly — show hex preview
                    print(f"  ECB first 64b hex: {ecb_result[:64].hex()}")
                    print(f"  CBC first 64b hex: {cbc_result[:64].hex()}")
                    # Show as lossy text
                    ecb_text = ecb_result[:200].decode("utf-8", errors="replace")
                    cbc_text = cbc_result[:200].decode("utf-8", errors="replace")
                    print(f"  ECB text: {repr(ecb_text[:100])}")
                    print(f"  CBC text: {repr(cbc_text[:100])}")

            except Exception as e:
                print(f"  Decrypt error: {e}")

        # Also show plain JSON responses from hellotalk
        elif "json" in ct and "hellotalk" in url:
            try:
                body = await response.body()
                data = json.loads(body)
                short = url.split("?")[0].replace("https://", "")
                print(f"  JSON {short}: {json.dumps(data, ensure_ascii=False)[:200]}")
            except Exception:
                pass

    page.on("response", on_response)

    print()
    print("=" * 60)
    print("  XTEA DECRYPTION MODE")
    print("  Intercepting and decrypting ht-enc traffic")
    print("  Browse HelloTalk in Chrome to generate traffic")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    # Reload to capture initial sync
    print("\nReloading page...")
    await page.reload(wait_until="networkidle", timeout=30000)
    print("Page loaded. Browse around to capture more.\n")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass

    # Save
    with open("captures/decrypted_traffic.json", "w") as f:
        json.dump(decrypted_messages, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nSaved {len(decrypted_messages)} decrypted messages to captures/decrypted_traffic.json")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
