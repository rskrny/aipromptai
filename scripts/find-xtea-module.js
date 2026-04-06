() => {
    var results = {};

    // Check webpackJsonp - it's the webpack entry point
    results.has_webpackJsonp = typeof webpackJsonp !== 'undefined';
    if (typeof webpackJsonp !== 'undefined') {
        results.webpackJsonp_type = typeof webpackJsonp;
        results.webpackJsonp_length = webpackJsonp.length;
        // webpackJsonp is typically an array of [chunkIds, modules, executeModules]
        // The modules object has all the module functions
        if (webpackJsonp.length > 0) {
            var first = webpackJsonp[0];
            results.first_entry_type = typeof first;
            if (Array.isArray(first) && first.length >= 2) {
                var modules = first[1];
                results.modules_type = typeof modules;
                if (typeof modules === 'object') {
                    var keys = Object.keys(modules);
                    results.module_count = keys.length;
                    results.module_keys_sample = keys.slice(0, 20);
                }
            }
        }
    }

    // Also check if the manifest.js set up a global require function
    results.has_window_require = typeof window.require !== 'undefined';
    results.has_window_webpackChunk = typeof window.webpackChunk !== 'undefined';

    // Search window for any object with xTEADecryptWithKey
    for (var k in window) {
        try {
            var v = window[k];
            if (v && typeof v === 'object' && typeof v.xTEADecryptWithKey === 'function') {
                results.found_xtea_on = k;
                break;
            }
            if (v && typeof v === 'object' && v.default && typeof v.default.xTEADecryptWithKey === 'function') {
                results.found_xtea_on = k + '.default';
                break;
            }
        } catch(e) {}
    }

    return results;
}
