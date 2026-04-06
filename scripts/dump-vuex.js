() => {
    const result = {};
    const app = document.querySelector('#app');
    if (app && app.__vue__ && app.__vue__.$store) {
        const state = app.__vue__.$store.state;
        const keys = Object.keys(state);
        result.vuex_keys = keys;
        for (const k of keys) {
            try {
                const val = JSON.stringify(state[k]);
                result['vuex_' + k] = val ? val.substring(0, 3000) : null;
            } catch(e) {
                result['vuex_' + k] = '[circular]';
            }
        }
    } else {
        result.error = 'no vue store found';
    }

    // Also check performance entries
    const entries = performance.getEntriesByType('resource');
    result.ht_resources = entries
        .filter(function(e) { return e.name.indexOf('hellotalk') > -1; })
        .map(function(e) { return {name: e.name.substring(0, 200), type: e.initiatorType, size: e.transferSize}; });

    return result;
}
