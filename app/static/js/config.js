// Konfigurasi path gambar
const AppConfig = (function() {
    'use strict';
    
    const config = {
        API_BASE_URL: window.location.origin + '/api',
        DEFAULT_POSTER: '/static/images/no-poster.svg',
        TMDB_IMAGE_BASE: 'https://image.tmdb.org/t/p/'
    };

    function getSafeImageUrl(path) {
        if (!path) {
            console.warn('Path gambar tidak tersedia, menggunakan gambar default');
            return config.DEFAULT_POSTER;
        }

        // Jika path sudah berupa URL lengkap atau data URI, gunakan langsung
        if (path.startsWith('http') || path.startsWith('data:')) {
            return path;
        }

        // Jika path dari TMDB (biasanya dimulai dengan /)
        if (path.startsWith('/') && !path.startsWith('/static/')) {
            return config.TMDB_IMAGE_BASE + 'w500' + path;
        }

        // Pastikan path lokal dimulai dengan /static/
        let finalPath = path;
        if (!finalPath.startsWith('/')) {
            finalPath = '/' + finalPath;
        }
        if (!finalPath.startsWith('/static/')) {
            finalPath = '/static' + (finalPath.startsWith('/') ? '' : '/') + finalPath;
        }
        
        return finalPath;
    }

    return {
        config: config,
        getSafeImageUrl: getSafeImageUrl
    };
})();
