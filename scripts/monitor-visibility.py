#!/usr/bin/env python3
"""Monitor discovery visibility — checks every 60s if the account becomes visible."""
import os, sys
os.environ['PYTHONIOENCODING'] = 'utf-8'

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
import httpx, json, time, gzip
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
auth = json.load(open(ROOT / 'captures/probe_auth.json'))
keys = json.load(open(ROOT / 'captures/our_keys.json'))
uid = auth['x-ht-uid']
aes_key = bytes.fromhex(keys['shared_secret'])

def decrypt(data, key):
    if len(data) == 0 or len(data) % 16 != 0:
        return data.decode('utf-8', errors='replace')
    c = Cipher(algorithms.AES(key), modes.ECB())
    d = c.decryptor()
    padded = d.update(data) + d.finalize()
    try:
        u = PKCS7(128).unpadder()
        raw = u.update(padded) + u.finalize()
    except:
        raw = padded
    if raw[:2] == b'\x1f\x8b':
        return gzip.decompress(raw).decode('utf-8')
    return raw.decode('utf-8')

headers = {
    'x-ht-version': '6.3.0', 'x-ht-os': 'ios', 'x-ht-uid': uid,
    'x-ht-did': auth['x-ht-did'], 'x-ht-timezone': '-10.00',
    'Authorization': auth['Authorization'],
    'User-Agent': f'ios;6.3.0;iPhone14,3;26.4;{uid}',
    'Accept': '*/*', 'x-ht-pub': keys['x_ht_pub'],
}

def check():
    client = httpx.Client(base_url='https://api-global.hellotalk8.com', timeout=15, headers=headers)
    now = datetime.now().strftime('%H:%M:%S')

    # 1. Check filter/search plan
    try:
        resp = client.get('/go_user_search/v2/filter', params={'userid': uid, 'learnlang': '2'})
        text = decrypt(resp.content, aes_key)
        data = json.loads(text)
        plan_status = data.get('msg', data.get('code', '?'))
    except:
        try:
            plan_status = resp.json().get('msg', '?')
        except:
            plan_status = '?'

    # 2. Check discovery page 1
    time.sleep(1)
    visible = False
    try:
        resp2 = client.get('/go_user_search/v2/recommend', params={
            'userid': uid, 'learnlang': '2', 'page': '1',
            'latitude': '20.7564', 'longitude': '-155.99',
        })
        text2 = decrypt(resp2.content, aes_key)
        data2 = json.loads(text2)
        results = data2.get('data', {}).get('results', []) if data2.get('data') else []
        visible = any(str(u.get('userid')) == uid for u in results)
        user_count = len(results)
    except:
        user_count = '?'

    client.close()

    status = "VISIBLE!" if visible else "invisible"
    print(f'[{now}] Search plan: {plan_status} | Discovery: {status} ({user_count} users)')

    if visible:
        print('\n*** YOU ARE NOW VISIBLE IN DISCOVERY! ***')
        return True
    if 'Failed' not in str(plan_status):
        print(f'\n*** SEARCH PLAN STATUS CHANGED: {plan_status} ***')
    return False

if __name__ == '__main__':
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print(f'Monitoring visibility every {interval}s. Ctrl+C to stop.')
    print(f'User: {uid}')
    print()
    try:
        while True:
            if check():
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print('\nStopped.')
