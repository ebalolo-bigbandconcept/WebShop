import axios from 'axios'

const client = axios.create({
    withCredentials: true,
});

const SAFE_METHODS = ['get', 'head', 'options', 'trace'];

const getCsrfToken = () => {
    if (typeof document === 'undefined') return null;
    const match = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('XSRF-TOKEN='));
    return match ? decodeURIComponent(match.split('=')[1]) : null;
};

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

    const method = (config.method || 'get').toLowerCase();
    if (!SAFE_METHODS.includes(method)) {
        const csrf = getCsrfToken();
        if (csrf) {
            config.headers = {
                ...config.headers,
                'X-CSRF-Token': csrf,
            };
        }
    }
    return config;
});

export default client;