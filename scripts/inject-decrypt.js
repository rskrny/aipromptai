async () => {
    // Inline the XTEA functions extracted from app.js
    var delta = 0x9E3779B9;

    function surrogatePair(code, idx, str) {
        return (64512 & code) === 55296 && idx + 1 < str.length && (64512 & str.charCodeAt(idx + 1)) === 56320;
    }

    function strToBytes(e) {
        var t = [], n = 0;
        for (var i = 0; i < e.length; i++) {
            var r = e.charCodeAt(i);
            if (r < 128) {
                t[n++] = r;
            } else if (r < 2048) {
                t[n++] = (r >> 6) | 192;
                t[n++] = (63 & r) | 128;
            } else if (surrogatePair(r, i, e)) {
                r = 65536 + ((1023 & r) << 10) + (1023 & e.charCodeAt(++i));
                t[n++] = (r >> 18) | 240;
                t[n++] = ((r >> 12) & 63) | 128;
                t[n++] = ((r >> 6) & 63) | 128;
                t[n++] = (63 & r) | 128;
            } else {
                t[n++] = (r >> 12) | 224;
                t[n++] = ((r >> 6) & 63) | 128;
                t[n++] = (63 & r) | 128;
            }
        }
        return t;
    }

    function strToKey(e) {
        var n = [], r = strToBytes(e);
        for (var s = 0; s < r.length; s += 4) {
            n[s >> 2] = (r[s] || 0) | ((r[s + 1] || 0) << 8) | ((r[s + 2] || 0) << 16) | ((r[s + 3] || 0) << 24);
        }
        return n;
    }

    function u32ToBytes(arr) {
        var out = [];
        for (var i = 0; i < arr.length; i++) {
            out.push(arr[i] & 255);
            out.push((arr[i] >>> 8) & 255);
            out.push((arr[i] >>> 16) & 255);
            out.push((arr[i] >>> 24) & 255);
        }
        return out;
    }

    function xteaDecryptBlock(v0, v1, key, rounds) {
        var total = ((delta * rounds) & 0xFFFFFFFF) >>> 0;
        for (var i = 0; i < rounds; i++) {
            v1 = (v1 - ((((v0 << 4 ^ v0 >>> 5) + v0) ^ (total + key[(total >>> 11) & 3])) >>> 0)) >>> 0;
            total = (total - delta) >>> 0;
            v0 = (v0 - ((((v1 << 4 ^ v1 >>> 5) + v1) ^ (total + key[total & 3])) >>> 0)) >>> 0;
        }
        return [v0 >>> 0, v1 >>> 0];
    }

    function xteaDecrypt(data, keyStr) {
        if (!data || !keyStr) return false;
        if (keyStr.length > 16) keyStr = keyStr.substr(0, 16);

        var key = strToKey(keyStr);
        var s = new Uint32Array(data);
        var o = data.byteLength || data.length;

        if (o < 1 || o % 8) return false;

        var c = [];
        var l = [0, 0];
        var d, m;

        // First block
        d = xteaDecryptBlock(s[0], s[1], key, 4);
        l[0] = d[0];
        l[1] = d[1];
        c[0] = d[0];
        c[1] = d[1];

        // Remaining blocks
        for (var idx = 2; idx < o / 4; idx += 2) {
            m = [(s[idx] ^ l[0]) >>> 0, (s[idx + 1] ^ l[1]) >>> 0];
            d = xteaDecryptBlock(m[0], m[1], key, 4);
            l[0] = d[0];
            l[1] = d[1];
            c[idx] = (d[0] ^ s[idx - 2]) >>> 0;
            c[idx + 1] = (d[1] ^ s[idx - 1]) >>> 0;
        }

        // Check last block for validity
        if (c[o / 4 - 1] || (4294967040 & c[o / 4 - 2])) {
            return {error: "bad tplain", last: c[o/4-1], secondLast: c[o/4-2]};
        }

        var f = 255 & c[0] & 7;
        var totalLen = 4 * (o / 4 + 1) - (f + 3);
        var h = u32ToBytes(c);

        for (var idx2 = 0; idx2 < totalLen; idx2++) {
            h[idx2] = h[f + 3 + idx2] || 0;
        }

        var p = o - (f + 3) - 7;
        h = h.slice(0, p);

        var decoded = new TextDecoder().decode(new Uint8Array(h));
        return decoded;
    }

    // Fetch and decrypt
    var uuid = "c27e30df-8c9c-4b48-94a7-0c66b0fa7cb6";
    var url = "https://web.hellotalk8.com/im/lg/sync/" + uuid + "/1?id=" + uuid;

    var resp = await fetch(url, {method: "POST"});
    var buf = await resp.arrayBuffer();

    var decrypted = xteaDecrypt(buf, uuid);

    if (typeof decrypted === 'string') {
        return {
            success: true,
            encrypted_size: buf.byteLength,
            decrypted_length: decrypted.length,
            preview: decrypted.substring(0, 5000)
        };
    } else {
        return {
            success: false,
            encrypted_size: buf.byteLength,
            result: decrypted
        };
    }
}
