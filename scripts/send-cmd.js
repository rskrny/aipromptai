async () => {
    // The IM protocol uses commands (cmd field)
    // cmd 38920 = getinfo (returns user online status)
    // cmd 16385 = message
    // cmd 28745 = card/notification
    //
    // The web client sends commands by POSTing XTEA-encrypted data
    // to the sync endpoint. Let's see if we can send custom commands
    // by capturing the send function.

    // First, let's see what the app sends when we interact
    window.__sent_data = [];

    // The app uses axios/XHR to POST to the sync endpoint
    // Hook the send to capture outgoing data
    var origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(body) {
        if (this._url && this._url.indexOf('hellotalk') > -1) {
            var entry = {url: this._url, time: Date.now()};
            if (body) {
                if (body instanceof ArrayBuffer) {
                    entry.type = 'arraybuffer';
                    entry.size = body.byteLength;
                } else if (typeof body === 'string') {
                    entry.type = 'string';
                    entry.body = body.substring(0, 500);
                } else {
                    entry.type = typeof body;
                    entry.size = body.length || body.byteLength || 0;
                }
            }
            window.__sent_data.push(entry);
        }
        return origSend.apply(this, arguments);
    };

    // Also reset captures to only get new data
    window.__decrypted_data = [];

    return {
        hooks: 'send capture installed',
        tip: 'Click on different chats and send a test message to capture outgoing protocol'
    };
}
