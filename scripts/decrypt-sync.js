async () => {
    // Fetch the sync endpoint and return the raw bytes
    const uuid = "c27e30df-8c9c-4b48-94a7-0c66b0fa7cb6";
    const url = "https://web.hellotalk8.com/im/lg/sync/" + uuid + "/1?id=" + uuid;

    const resp = await fetch(url, {method: "POST"});
    const ct = resp.headers.get("content-type");
    const buf = await resp.arrayBuffer();
    const arr = new Uint8Array(buf);

    // Return first 2000 bytes as hex for analysis
    const hex = Array.from(arr.slice(0, 2000)).map(function(b) { return b.toString(16).padStart(2, '0'); }).join('');

    return {
        status: resp.status,
        ct: ct,
        size: arr.length,
        hex: hex
    };
}
