import axios from 'axios'

const client = axios.create({
    withCredentials: true,
});

// Rewrite insecure absolute HTTP API calls to same-origin /api when page is HTTPS.
// Avoids mixed-content and insecure download blocks when backend lacks TLS.
client.interceptors.request.use((config) => {
    try {
        const url = config.url || '';
        if (typeof window !== 'undefined' && window.location.protocol === 'https:' && /^http:\/\//i.test(url)) {
            const parsed = new URL(url);
            const path = parsed.pathname + (parsed.search || '') + (parsed.hash || '');
            config.url = `/api${path.startsWith('/') ? '' : '/'}${path}`;
        }
    } catch (e) {
        // noop: if URL parsing fails, keep original config
    }
    return config;
});

export default client;