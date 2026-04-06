async () => {
    var captured = [];

    var page = window.open('https://www.hellotalk.com/u/u_sam749');

    // Wait for it to load
    await new Promise(r => setTimeout(r, 5000));

    // Can't access cross-origin page. Let's try fetching the API directly instead.
    // The profile page likely calls an API like /api/user/profile?username=u_sam749

    var endpoints = [
        'https://api-global.hellotalk8.com/api/v1/user/profile?username=u_sam749',
        'https://www.hellotalk.com/api/user/profile?username=u_sam749',
        'https://www.hellotalk.com/api/v1/user?username=u_sam749',
    ];

    for (var url of endpoints) {
        try {
            var resp = await fetch(url);
            var text = await resp.text();
            captured.push({url: url, status: resp.status, body: text.substring(0, 500)});
        } catch(e) {
            captured.push({url: url, error: e.message});
        }
    }

    if (page) page.close();
    return captured;
}
