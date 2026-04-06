(() => {
    if (window.__cdp_hooks) return;
    window.__cdp_hooks = true;
    window.__decrypted_data = [];

    // The app uses axios or XHR with responseType: arraybuffer
    // Then decrypts the ArrayBuffer response with xTEADecryptWithKey
    // The decrypted result is a string (JSON)

    // Hook: intercept the XHR responseText/response after load
    // But encrypted responses come as ArrayBuffer - we can't read those

    // Better approach: Hook JSON.parse to catch the moment
    // the decrypted string is parsed into an object
    var origParse = JSON.parse;
    JSON.parse = function(text) {
        var result = origParse.apply(this, arguments);
        // Capture large JSON objects that look like HelloTalk data
        if (typeof text === 'string' && text.length > 100) {
            try {
                var str = typeof result === 'object' ? JSON.stringify(result) : '';
                // Check if it contains HelloTalk-related fields
                var isHT = str.indexOf('user_id') > -1 ||
                           str.indexOf('uid') > -1 ||
                           str.indexOf('msg_id') > -1 ||
                           str.indexOf('moments') > -1 ||
                           str.indexOf('chat') > -1 ||
                           str.indexOf('lang') > -1 ||
                           str.indexOf('hellotalk') > -1 ||
                           str.indexOf('nickname') > -1 ||
                           str.indexOf('avatar') > -1;

                if (isHT || text.length > 500) {
                    window.__decrypted_data.push({
                        size: text.length,
                        text: text.substring(0, 10000),
                        time: Date.now()
                    });
                }
            } catch(e) {}
        }
        return result;
    };

    // Also hook the Uint8Array constructor to see what's being decrypted
    // The xTEA decrypt creates new Uint8Array(h) at the end
    // Actually let's just hook TextDecoder which is called at the very end
    var origDecode = TextDecoder.prototype.decode;
    TextDecoder.prototype.decode = function(input) {
        var result = origDecode.apply(this, arguments);
        if (result && result.length > 100) {
            window.__decrypted_data.push({
                source: 'TextDecoder',
                size: result.length,
                text: result.substring(0, 10000),
                time: Date.now()
            });
        }
        return result;
    };
})()
