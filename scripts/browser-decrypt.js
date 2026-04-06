async () => {
    var uuid = "c27e30df-8c9c-4b48-94a7-0c66b0fa7cb6";
    var url = "https://web.hellotalk8.com/im/lg/sync/" + uuid + "/1?id=" + uuid;

    var resp = await fetch(url, {method: "POST"});
    var buf = await resp.arrayBuffer();

    // Find the xTEA module in webpack
    var xtea = null;
    if (window.__webpack_require__) {
        var cache = window.__webpack_require__.c;
        var ids = Object.keys(cache);
        for (var i = 0; i < ids.length; i++) {
            var mod = cache[ids[i]];
            if (mod && mod.exports && mod.exports.default && typeof mod.exports.default.xTEADecryptWithKey === 'function') {
                xtea = mod.exports.default;
                break;
            }
        }
    }

    if (!xtea) {
        // Try to find it as a global or on any object
        return {error: "xTEA module not found in webpack cache", webpack_require: !!window.__webpack_require__};
    }

    // Decrypt using the app's own function
    var decrypted = xtea.xTEADecryptWithKey(buf, uuid);

    if (decrypted === false) {
        return {error: "decryption returned false", size: buf.byteLength};
    }

    return {
        success: true,
        size: buf.byteLength,
        decrypted_length: decrypted.length,
        decrypted_preview: decrypted.substring(0, 5000)
    };
}
