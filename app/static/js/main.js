/**
 * Aplikasi Rekomendasi Film - Main JavaScript
 * @version 1.1.0
 */

// Create a new App object
var App = (function() {
    'use strict';
    
    // Private variables
    var currentMovies = [];
    var activeTab = 'trending';
    var currentPage = 1;
    var isLoading = false;
    
    // Configuration
    var config = window.APP_CONFIG || {
        API_BASE_URL: window.location.origin + '/api',
        DEFAULT_POSTER: window.location.origin + '/static/images/no-poster.svg',
        TMDB_IMAGE_BASE: 'https://image.tmdb.org/t/p/',
        POSTER_SIZES: {
            small: 'w185',
            medium: 'w342',
            large: 'w500',
            original: 'original'
        }
    };
    
    // Helper functions
    function getApiUrl(endpoint) {
        return config.API_BASE_URL + (endpoint.startsWith('/') ? endpoint : '/' + endpoint);
    }
    
    function getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }
    
    // Private function to create movie card
    function createMovieCard(movie) {
        if (!movie || !movie.id) {
            console.error('Invalid movie data:', movie);
            return null;
        }

        console.log('Membuat kartu film:', movie.title || movie.name);

        // Handle poster path yang berbeda-beda
        let posterPath = movie.poster_path || movie.poster || '';

        // Jika posterPath sudah merupakan URL lengkap, gunakan langsung
        let posterUrl = posterPath;

        // Jika bukan URL lengkap, gunakan getSafeImageUrl
        if (posterPath && !posterPath.startsWith('http')) {
            posterUrl = getSafeImageUrl(posterPath, 'w500');
        }

        // Jika tidak ada poster, gunakan default
        if (!posterPath) {
            posterUrl = config.DEFAULT_POSTER;
        }

        const card = document.createElement('div');
        card.className = 'movie-card';
        card.setAttribute('data-movie-id', movie.id);

        // Buat elemen card secara manual untuk kontrol yang lebih baik
        const posterDiv = document.createElement('div');
        posterDiv.className = 'movie-poster';

        const img = document.createElement('img');
        img.alt = movie.title || movie.name || 'Movie Poster';
        img.loading = 'lazy';
        img.setAttribute('data-movie-id', movie.id);

        // Tambahkan event listener untuk menangani load dan error
        img.onload = function() {
            this.classList.add('loaded');
        };

        img.onerror = function() {
            this.onerror = null; // Mencegah loop error
            this.src = config.DEFAULT_POSTER;
            this.style.objectFit = 'contain';
            this.style.padding = '20px';
            this.classList.add('loaded'); // Pastikan gambar default tetap terlihat
        };

        // Setel sumber gambar
        img.src = posterUrl;

        // Rating Badge (new design)
        const ratingBadge = document.createElement('div');
        ratingBadge.className = 'movie-rating-badge';

        // Pastikan vote_average ada dan valid
        let voteAvg = 'N/A';
        const voteSource = movie.vote_average !== undefined ? movie : (movie.original_data || {});

        if (voteSource.vote_average !== undefined && voteSource.vote_average !== null && voteSource.vote_average !== 0) {
            const rating = parseFloat(voteSource.vote_average);
            if (!isNaN(rating) && rating >= 0 && rating <= 10) {
                voteAvg = rating.toFixed(1);
            }
        }

        ratingBadge.innerHTML = `<i class="fas fa-star"></i> ${voteAvg}`;

        // Buat elemen info film
        const infoDiv = document.createElement('div');
        infoDiv.className = 'movie-info';

        const title = document.createElement('h3');
        title.className = 'movie-title';
        title.textContent = movie.title || movie.name || 'Judul tidak tersedia';
        title.setAttribute('data-movie-id', movie.id);

        const metaDiv = document.createElement('div');
        metaDiv.className = 'movie-meta';

        const yearSpan = document.createElement('span');
        yearSpan.className = 'movie-year';

        // Validasi dan format tahun rilis
        let releaseYear = 'Tahun tidak tersedia';
        if (movie.release_date) {
            try {
                const date = new Date(movie.release_date);
                if (!isNaN(date.getTime())) {
                    releaseYear = date.getFullYear().toString();
                }
            } catch (e) {
                console.warn('Error parsing release date:', e);
            }
        } else if (movie.first_air_date) {
            try {
                const date = new Date(movie.first_air_date);
                if (!isNaN(date.getTime())) {
                    releaseYear = date.getFullYear().toString();
                }
            } catch (e) {
                console.warn('Error parsing first air date:', e);
            }
        }

        yearSpan.textContent = releaseYear;

        // Genre tags - improved version
        const genresContainer = document.createElement('div');
        genresContainer.className = 'movie-genres';

        // Prioritas: genres (array objects) > genre_ids (array numbers) > genres string
        let genreNames = [];

        if (movie.genres && Array.isArray(movie.genres)) {
            if (movie.genres.length > 0 && typeof movie.genres[0] === 'object') {
                // Array of genre objects
                genreNames = movie.genres.slice(0, 2).map(g => g.name || g).filter(name => name);
            } else if (movie.genres.length > 0 && typeof movie.genres[0] === 'string') {
                // Array of genre strings
                genreNames = movie.genres.slice(0, 2);
            }
        } else if (movie.genre_ids && Array.isArray(movie.genre_ids)) {
            // Fallback to genre_ids - would need genre mapping
            genreNames = movie.genre_ids.slice(0, 2).map(id => `Genre ${id}`);
        }

        genreNames.forEach(genreName => {
            const genreTag = document.createElement('span');
            genreTag.className = 'genre-tag';
            genreTag.textContent = genreName;
            genresContainer.appendChild(genreTag);
        });

        // Gabungkan semua elemen
        posterDiv.appendChild(img);
        posterDiv.appendChild(ratingBadge);

        metaDiv.appendChild(yearSpan);
        if (genresContainer.children.length > 0) {
            metaDiv.appendChild(genresContainer);
        }

        infoDiv.appendChild(title);
        infoDiv.appendChild(metaDiv);

        card.appendChild(posterDiv);
        card.appendChild(infoDiv);

        // Add click event listener for movie details dengan error handling
        card.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const movieId = this.getAttribute('data-movie-id') || movie.id;
            if (movieId) {
                showMovieDetails(movieId);
            } else {
                console.error('Movie ID not found for card click');
                showError('ID film tidak ditemukan');
            }
        });

        return card;
    }
    
    // Private function to apply stored filters
    function applyStoredFilters() {
        try {
            const savedFilters = localStorage.getItem('activeFilters');
            if (!savedFilters) return null;

            const filters = JSON.parse(savedFilters);
            const genreId = filters.genreId || '';
            const year = filters.year || '';

            console.log('Applying stored filters:', filters);

            // Set filter values in the form
            const genreSelect = document.getElementById('genre-filter');
            const yearSelect = document.getElementById('year-filter');

            if (genreSelect) {
                genreSelect.value = genreId;
            }

            if (yearSelect) {
                yearSelect.value = year;
            }

            return filters;

        } catch (error) {
            console.error('Gagal menerapkan filter yang disimpan:', error);
            return { genreId: '', year: '' };
        }
    }
    
    // Private function to load genres
    async function loadGenres() {
        const genreSelect = document.getElementById('genre-filter');
        if (!genreSelect) return;
        
        try {
            // Tampilkan loading
            genreSelect.innerHTML = '<option value="">Memuat genre...</option>';
            
            // Coba terapkan filter yang disimpan
            const storedFilters = applyStoredFilters();
            
            try {
                const response = await fetch(getApiUrl('/genres'), {
                    headers: getHeaders(),
                    cache: 'no-cache'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Kosongkan select dan tambahkan opsi default
                genreSelect.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Semua Genre';
                genreSelect.appendChild(defaultOption);
                
                // Pastikan data.genres ada dan merupakan array
                if (!data.genres || !Array.isArray(data.genres)) {
                    throw new Error('Format data genre tidak valid');
                }
                
                // Urutkan genre berdasarkan nama
                const sortedGenres = [...data.genres].sort((a, b) => 
                    a.name.localeCompare(b.name, 'id', {sensitivity: 'base'})
                );
                
                // Tambahkan setiap genre ke dropdown
                sortedGenres.forEach(genre => {
                    // Skip tahun (kita akan menanganinya di loadYears)
                    if (parseInt(genre.id) >= 20000) return;
                    
                    const option = document.createElement('option');
                    option.value = genre.id.toString();
                    option.textContent = genre.name;
                    genreSelect.appendChild(option);
                });
                
                console.log('Genre berhasil dimuat:', sortedGenres.length, 'genre');
                
                // Setel ulang filter yang disimpan
                applyStoredFilters();
                
            } catch (error) {
                console.error('Gagal memuat genre:', error);
                genreSelect.innerHTML = '<option value="">Gagal memuat genre</option>';
                
                // Coba muat ulang setelah 5 detik jika gagal
                setTimeout(() => loadGenres(), 5000);
            }
        } catch (error) {
            console.error('Gagal memuat genre:', error);
        }
    }

    // Private function to load years
    async function loadYears() {
        try {
            const yearSelect = document.getElementById('year-filter');
            
            if (yearSelect) {
                yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
                
                // Tambahkan tahun dari 2000 sampai 2025 (terurut dari terbaru)
                for (let year = 2025; year >= 2000; year--) {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    yearSelect.appendChild(option);
                }
            }
        } catch (error) {
            console.error('Gagal memuat tahun:', error);
        }
    }

    // Private function to show error
    function showError(message) {
        const errorContainer = document.getElementById('error-container');
        if (!errorContainer) return;

        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.innerHTML = `
            <span>${message}</span>
            <button class="close-error">&times;</button>
        `;

        errorContainer.appendChild(errorElement);
        errorContainer.style.display = 'block';

        // Tambahkan event listener untuk tombol tutup
        const closeButton = errorElement.querySelector('.close-error');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                errorElement.remove();
                if (errorContainer.children.length === 0) {
                    errorContainer.style.display = 'none';
                }
            });
        }

        // Sembunyikan error setelah 5 detik
        setTimeout(() => {
            errorElement.remove();
            if (errorContainer.children.length === 0) {
                errorContainer.style.display = 'none';
            }
        }, 5000);
    }

    // Private function to load movies
    async function loadMovies(type = 'popular', page = 1, genreId = '', year = '') {
        // Pastikan type valid
        const validTypes = ['popular', 'newest', 'trending', 'top_rated'];
        if (!validTypes.includes(type)) {
            console.warn(`Tipe ${type} tidak valid, default ke 'popular'`);
            type = 'popular';
        }

        const loading = document.getElementById('loading');
        const container = document.getElementById(`${type}-movies`);
        const paginationContainer = document.getElementById(`${type}-pagination`);

        if (!container) {
            console.error(`Container not found for type: ${type}`);
            return;
        }

        try {
            // Tampilkan loading
            if (loading) loading.style.display = 'flex';
            container.innerHTML = '<div class="loading">Memuat film...</div>';

            // Pastikan nilai kosong diubah menjadi string kosong
            genreId = (genreId !== null && genreId !== undefined) ? genreId : '';
            year = (year !== null && year !== undefined) ? year : '';

            console.log(`Memuat film - Tipe: ${type}, Halaman: ${page}, Genre: ${genreId}, Tahun: ${year}`);

            // Bangun URL dengan parameter
            let url = getApiUrl(`/movies?type=${type}&page=${page}`);

            // Tambahkan parameter genre jika ada (cek lebih ketat)
            if (genreId && genreId !== 'undefined' && genreId !== 'null' && genreId !== '0' && genreId.trim() !== '') {
                url += `&genre=${encodeURIComponent(genreId)}`;
            }

            // Tambahkan parameter tahun jika ada (cek lebih ketat)
            if (year && year !== 'undefined' && year !== 'null' && year.trim() !== '' && /^\d{4}$/.test(year)) {
                url += `&year=${encodeURIComponent(year)}`;
            }

            console.log('URL yang diminta:', url);

            // Lakukan request ke API dengan timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 detik timeout

            const response = await fetch(url, {
                method: 'GET',
                headers: getHeaders(),
                cache: 'no-store',
                credentials: 'same-origin',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('API Response:', data);
            
            // Cek struktur data yang diterima
            const movies = data.results || data.movies || [];
            console.log(`Ditemukan ${movies.length} film`);
            
            // Update UI dengan data film
            container.innerHTML = '';
            if (Array.isArray(movies) && movies.length > 0) {
                const fragment = document.createDocumentFragment();
                movies.forEach(movie => {
                    if (movie && movie.id) {
                        try {
                            const movieCard = createMovieCard(movie);
                            if (movieCard) {
                                fragment.appendChild(movieCard);
                            }
                        } catch (error) {
                            console.error('Gagal membuat kartu film:', error);
                        }
                    }
                });
                container.appendChild(fragment);
            } else {
                container.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-film"></i>
                        <p>Tidak ada film yang ditemukan untuk kriteria ini</p>
                        <p class="no-results-hint">Coba ubah filter genre atau tahun, atau hapus filter untuk melihat semua film</p>
                    </div>`;
            }

            // Update pagination jika tersedia
            if (paginationContainer) {
                const totalPages = data.total_pages || 1;
                if (totalPages > 1) {
                    updatePagination(paginationContainer, type, data.page || 1, totalPages, genreId, year);
                } else {
                    paginationContainer.innerHTML = '';
                }
            }

            // Tandai tab sebagai sudah dimuat
            const section = container.closest('.movie-section');
            if (section) {
                section.setAttribute('data-loaded', 'true');
            }

            // Trigger event bahwa konten tab sudah dimuat
            const event = new CustomEvent('tabContentLoaded', { detail: { tabId: type } });
            document.dispatchEvent(event);

            return data;

        } catch (error) {
            console.error(`Gagal memuat film ${type}:`, error);
            if (container) {
                container.innerHTML = `
                    <div class="error-message">
                        <p>Gagal memuat film. ${error.message}</p>
                        <button class="btn-retry" onclick="loadMovies('${type}', ${page}, '${genreId || ''}', '${year || ''}')">
                            <i class="fas fa-sync-alt"></i> Coba Lagi
                        </button>
                    </div>`;
            }
            throw error;
        } finally {
            if (loading) loading.style.display = 'none';
        }
    }

    // Private function to get safe image URL
    function getSafeImageUrl(path, size = 'w500') {
        return config.TMDB_IMAGE_BASE + size + path;
    }

    // Private function to apply filters
    function applyFilters() {
        try {
            console.log('Menerapkan filter...');

            const genreSelect = document.getElementById('genre-filter');
            const yearSelect = document.getElementById('year-filter');

            // Validasi input
            if (!genreSelect || !yearSelect) {
                console.error('Elemen filter tidak ditemukan');
                return;
            }

            // Get filter values
            const genreId = genreSelect.value;
            const year = yearSelect.value;

            console.log('Filter values:', { genreId, year });

            // Save filters to localStorage
            localStorage.setItem('activeFilters', JSON.stringify({ genreId, year }));

            // Reload movies with filters for all tabs
            const tabs = ['trending', 'newest', 'popular'];
            tabs.forEach(tabId => {
                loadMovies(tabId, 1, genreId, year);
            });

        } catch (error) {
            console.error('Error applying filters:', error);
            showError('Gagal menerapkan filter');
        }
    }

    // Private function to clear filters
    function clearFilters() {
        try {
            console.log('Menghapus filter genre dan tahun...');

            const genreSelect = document.getElementById('genre-filter');
            const yearSelect = document.getElementById('year-filter');

            // Reset only filter values (genre and year)
            if (genreSelect) genreSelect.value = '';
            if (yearSelect) yearSelect.value = '';

            // Clear filter-related localStorage
            localStorage.removeItem('activeFilters');

            // Reload movies with cleared filters for all tabs
            const tabs = ['trending', 'newest', 'popular'];
            tabs.forEach(tabId => {
                const container = document.getElementById(`${tabId}-movies`);
                if (container && container.hasAttribute('data-search-results')) {
                    // In search mode - reload search results without filters
                    const searchQuery = container.getAttribute('data-search-query');
                    if (searchQuery) {
                        performSearchWithQuery(searchQuery, '', '');
                    }
                } else {
                    // Normal mode - reload movies without filters
                    loadMovies(tabId, 1, '', '');
                }
            });

        } catch (error) {
            console.error('Error clearing filters:', error);
            showError('Gagal menghapus filter');
        }
    }

    // Private function to reset search (separate from clear filters)
    function resetSearch() {
        try {
            console.log('Mereset pencarian...');

            const searchInput = document.getElementById('search-input');

            // Clear search input
            if (searchInput) searchInput.value = '';

            // Reset to normal mode
            resetToNormalMode();

        } catch (error) {
            console.error('Error resetting search:', error);
            showError('Gagal mereset pencarian');
        }
    }

    // Private function to perform search with specific filters
    function performSearchWithQuery(query, genreId, year) {
        console.log('Performing search with filters:', { query, genreId, year });

        // Show loading state
        const searchResultsSection = document.getElementById('search-results-section');
        const searchResults = document.getElementById('search-results');
        const searchResultsCount = document.getElementById('search-results-count');

        if (searchResultsSection) {
            searchResultsSection.style.display = 'block';
        }

        if (searchResults) {
            searchResults.innerHTML = '<div class="loading">Mencari film...</div>';
        }

        if (searchResultsCount) {
            searchResultsCount.textContent = 'Mencari...';
        }

        // Build URL with filters
        let url = getApiUrl('search?q=' + encodeURIComponent(query));
        if (genreId && genreId !== '') {
            url += '&genre=' + encodeURIComponent(genreId);
        }
        if (year && year !== '') {
            url += '&year=' + encodeURIComponent(year);
        }

        // Make API call
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('Search results with filters:', data);

                if (data.status === 'success') {
                    displaySearchResults(data);
                } else {
                    showSearchError(data.message || 'Terjadi kesalahan saat pencarian');
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                showSearchError('Terjadi kesalahan saat pencarian');
            });
    }

    // Private function to update pagination
    function updatePagination(container, type, currentPage, totalPages, genreId = '', year = '') {
        if (!container) return;

        container.innerHTML = '';

        // Don't show pagination if only one page
        if (totalPages <= 1) return;

        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'pagination';

        // Previous button
        if (currentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.className = 'page-btn prev-btn';
            prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i> Sebelumnya';
            prevBtn.addEventListener('click', () => loadMovies(type, currentPage - 1, genreId, year));
            paginationDiv.appendChild(prevBtn);
        }

        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        // First page
        if (startPage > 1) {
            const firstBtn = document.createElement('button');
            firstBtn.className = 'page-btn';
            firstBtn.textContent = '1';
            firstBtn.addEventListener('click', () => loadMovies(type, 1, genreId, year));
            paginationDiv.appendChild(firstBtn);

            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.className = 'pagination-dots';
                dots.textContent = '...';
                paginationDiv.appendChild(dots);
            }
        }

        // Page range
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
            pageBtn.textContent = i;
            pageBtn.addEventListener('click', () => loadMovies(type, i, genreId, year));
            paginationDiv.appendChild(pageBtn);
        }

        // Last page
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const dots = document.createElement('span');
                dots.className = 'pagination-dots';
                dots.textContent = '...';
                paginationDiv.appendChild(dots);
            }

            const lastBtn = document.createElement('button');
            lastBtn.className = 'page-btn';
            lastBtn.textContent = totalPages;
            lastBtn.addEventListener('click', () => loadMovies(type, totalPages, genreId, year));
            paginationDiv.appendChild(lastBtn);
        }

        // Next button
        if (currentPage < totalPages) {
            const nextBtn = document.createElement('button');
            nextBtn.className = 'page-btn next-btn';
            nextBtn.innerHTML = 'Selanjutnya <i class="fas fa-chevron-right"></i>';
            nextBtn.addEventListener('click', () => loadMovies(type, currentPage + 1, genreId, year));
            paginationDiv.appendChild(nextBtn);
        }

        container.appendChild(paginationDiv);
    }

    // Private function to display movie details in modal
    function displayMovieDetails(movie) {
        if (!movie || !movie.id) {
            console.error('Invalid movie data for modal:', movie);
            showError('Data film tidak valid');
            return;
        }

        console.log('Menampilkan detail film:', movie.title || movie.name);

        const modal = document.getElementById('movie-modal');
        const modalBody = modal ? modal.querySelector('.modal-body') : null;

        if (!modal || !modalBody) {
            console.error('Modal tidak ditemukan');
            showError('Modal tidak dapat dibuka');
            return;
        }

        // Handle poster path dengan validasi
        let posterUrl = movie.poster_path || movie.poster || '';
        if (posterUrl && !posterUrl.startsWith('http')) {
            posterUrl = getSafeImageUrl(posterUrl, 'w500');
        }
        if (!posterUrl) {
            posterUrl = config.DEFAULT_POSTER;
        }

        // Handle release date dengan validasi yang lebih ketat
        let releaseYear = 'Tahun tidak tersedia';
        if (movie.release_date) {
            try {
                const date = new Date(movie.release_date);
                if (!isNaN(date.getTime()) && date.getFullYear() > 1900 && date.getFullYear() <= new Date().getFullYear() + 2) {
                    releaseYear = date.getFullYear().toString();
                }
            } catch (e) {
                console.warn('Error parsing release date:', e);
            }
        } else if (movie.first_air_date) {
            try {
                const date = new Date(movie.first_air_date);
                if (!isNaN(date.getTime()) && date.getFullYear() > 1900 && date.getFullYear() <= new Date().getFullYear() + 2) {
                    releaseYear = date.getFullYear().toString();
                }
            } catch (e) {
                console.warn('Error parsing first air date:', e);
            }
        }

        // Handle rating dengan validasi range
        let rating = 'N/A';
        if (movie.vote_average !== undefined && movie.vote_average !== null && movie.vote_average !== 0) {
            const ratingValue = parseFloat(movie.vote_average);
            if (!isNaN(ratingValue) && ratingValue >= 0 && ratingValue <= 10) {
                rating = ratingValue.toFixed(1);
            }
        }

        // Handle genres dengan validasi yang lebih baik
        let genresHtml = '';
        if (movie.genres && Array.isArray(movie.genres) && movie.genres.length > 0) {
            const validGenres = movie.genres
                .map(genre => {
                    if (typeof genre === 'string' && genre.trim()) {
                        return `<span class="genre-tag">${genre.trim()}</span>`;
                    } else if (typeof genre === 'object' && genre && genre.name && genre.name.trim()) {
                        return `<span class="genre-tag">${genre.name.trim()}</span>`;
                    }
                    return '';
                })
                .filter(tag => tag)
                .slice(0, 5); // Maksimal 5 genre

            genresHtml = validGenres.join(' ');
        }

        // Handle overview dengan sanitasi
        let overview = movie.overview || 'Deskripsi tidak tersedia';
        if (typeof overview === 'string') {
            // Sanitasi dasar - hapus HTML tags berbahaya
            overview = overview.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
            overview = overview.replace(/<[^>]*>/g, ''); // Remove all HTML tags
            overview = overview.trim();
            if (!overview) {
                overview = 'Deskripsi tidak tersedia';
            }
        }

        // Handle vote count (jumlah penonton) dengan validasi
        let voteCount = 'N/A';
        if (movie.vote_count !== undefined && movie.vote_count !== null && movie.vote_count !== 0) {
            const count = parseInt(movie.vote_count);
            if (!isNaN(count) && count >= 0) {
                // Format angka dengan pemisah ribuan
                voteCount = count.toLocaleString('id-ID');
            }
        } else {
            // Jika vote_count tidak tersedia, coba gunakan data dari original_data
            if (movie.original_data && movie.original_data.vote_count !== undefined) {
                const count = parseInt(movie.original_data.vote_count);
                if (!isNaN(count) && count >= 0) {
                    voteCount = count.toLocaleString('id-ID');
                }
            }
        }

        // Handle director (sutradara) - jika ada di original_data
        let director = 'Tidak tersedia';
        if (movie.original_data && movie.original_data.director) {
            director = String(movie.original_data.director).trim() || 'Tidak tersedia';
        }

        // Handle runtime jika ada
        let runtime = '';
        if (movie.runtime) {
            const runtimeValue = parseInt(movie.runtime);
            if (!isNaN(runtimeValue) && runtimeValue > 0) {
                runtime = `<span class="modal-runtime"><i class="fas fa-clock"></i> ${runtimeValue} menit</span>`;
            }
        }

        // Build modal content dengan struktur yang lebih aman
        const modalContent = `
            <button class="modal-close" aria-label="Tutup">&times;</button>
            <div class="modal-body">
                <div class="modal-poster-container">
                    <img id="modal-poster" class="modal-poster" src="${posterUrl}" alt="${(movie.title || movie.name || 'Movie Poster').replace(/"/g, '"')}" onerror="this.src='${config.DEFAULT_POSTER}'">
                </div>
                <div class="modal-info">
                    <h2 id="modal-title">${(movie.title || movie.name || 'Judul tidak tersedia').replace(/</g, '<').replace(/>/g, '>')}</h2>
                    <div class="modal-meta">
                        <span id="modal-year">${releaseYear}</span>
                        <span class="modal-rating">
                            <i class="fas fa-star"></i>
                            <span id="modal-rating">${rating}</span>
                        </span>
                        <span class="modal-vote-count">
                            <i class="fas fa-users"></i>
                            <span id="modal-vote-count">${voteCount}</span> penonton
                        </span>
                        ${runtime}
                    </div>
                    <div class="modal-genres" id="modal-genres">
                        ${genresHtml}
                    </div>
                    <div class="modal-director">
                        <strong>Sutradara:</strong> <span id="modal-director">${director.replace(/</g, '<').replace(/>/g, '>')}</span>
                    </div>
                    <h3>Sinopsis</h3>
                    <p id="modal-overview" class="modal-overview">${overview.replace(/</g, '<').replace(/>/g, '>')}</p>
                    <div class="modal-actions">
                        <button id="add-to-favorites" class="btn btn-secondary" data-movie-id="${movie.id}">
                            <i class="fas fa-heart"></i> Favorit
                        </button>
                    </div>
                </div>
            </div>
        `;

        modalBody.innerHTML = modalContent;

        // Add event listeners for modal actions dengan cleanup
        const closeBtn = modalBody.querySelector('.modal-close');
        if (closeBtn) {
            const closeHandler = () => {
                modal.style.display = 'none';
                // Cleanup event listeners
                closeBtn.removeEventListener('click', closeHandler);
                modal.removeEventListener('click', outsideClickHandler);
                document.removeEventListener('keydown', escapeHandler);
            };

            const outsideClickHandler = (e) => {
                if (e.target === modal) {
                    closeHandler();
                }
            };

            const escapeHandler = (e) => {
                if (e.key === 'Escape') {
                    closeHandler();
                    document.removeEventListener('keydown', escapeHandler);
                }
            };

            closeBtn.addEventListener('click', closeHandler);
            modal.addEventListener('click', outsideClickHandler);
            document.addEventListener('keydown', escapeHandler);
        }

        // Show modal
        modal.style.display = 'block';

        // Focus management untuk accessibility
        modal.focus();
    }

    // Private function to show movie details
    function showMovieDetails(movieId) {
        console.log('Menampilkan detail film:', movieId);

        if (!movieId) {
            console.error('Movie ID tidak valid');
            showError('ID film tidak valid');
            return;
        }

        // Validasi movieId - harus string atau number yang valid
        const validMovieId = String(movieId).trim();
        if (!validMovieId || validMovieId === 'undefined' || validMovieId === 'null') {
            console.error('Movie ID tidak valid:', movieId);
            showError('ID film tidak valid');
            return;
        }

        // Show loading in modal
        const modal = document.getElementById('movie-modal');
        const modalBody = modal ? modal.querySelector('.modal-body') : null;

        if (!modal || !modalBody) {
            console.error('Modal tidak ditemukan');
            showError('Modal tidak dapat dibuka');
            return;
        }

        // Show modal with loading state
        modal.style.display = 'block';
        modalBody.innerHTML = `
            <div class="modal-loading">
                <div class="spinner"></div>
                <p>Memuat detail film...</p>
            </div>
        `;

        // Fetch movie details from API dengan timeout dan error handling yang lebih baik
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 detik timeout

        fetch(getApiUrl(`/movie/${encodeURIComponent(validMovieId)}`), {
            method: 'GET',
            headers: getHeaders(),
            signal: controller.signal,
            cache: 'no-cache'
        })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Film tidak ditemukan');
                } else if (response.status === 500) {
                    throw new Error('Terjadi kesalahan server');
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }
            return response.json();
        })
        .then(data => {
            // Debug: tampilkan respons API untuk inspeksi
            console.log('Movie detail API response:', data);

            // Terima beberapa bentuk response umum
            let movieData = null;
            if (data && data.status === 'success' && data.data) movieData = data.data;
            else if (data && data.movie) movieData = data.movie;
            else if (data && data.result) movieData = data.result;
            else if (data && data.id) movieData = data;
            else if (Array.isArray(data) && data.length > 0 && data[0] && data[0].id) movieData = data[0];

            if (movieData) {
                displayMovieDetails(movieData);
            } else {
                throw new Error(data && data.message ? data.message : 'Data film tidak valid');
            }
        })
       .catch(error => {
            clearTimeout(timeoutId);
            console.error('Error loading movie details:', error);
            let errorMessage = 'Terjadi kesalahan saat memuat detail film';
            if (error.name === 'AbortError') {
                errorMessage = 'Waktu memuat habis. Silakan coba lagi.';
            } else if (error.message) {
                errorMessage = error.message;
            }
            modalBody.innerHTML = `
                <div class="modal-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Gagal Memuat Detail Film</h3>
                    <p>${errorMessage}</p>
                    <div class="modal-error-actions">
                        <button class="btn btn-secondary" onclick="document.getElementById('movie-modal').style.display='none'">
                            Tutup
                        </button>
                        <button class="btn btn-primary" onclick="App.showMovieDetails('${validMovieId}')">
                            <i class="fas fa-sync-alt"></i> Coba Lagi
                        </button>
                    </div>
                </div>
            `;
        });
    }
    // Private function to initialize tabs
    function initTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const movieSections = document.querySelectorAll('.movie-section');

        console.log('Initializing tabs, found buttons:', tabButtons.length);
        console.log('Found sections:', movieSections.length);

        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tabId = this.getAttribute('data-tab');
                console.log('Tab clicked:', tabId);

                // Update active tab
                tabButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                // Update active section
                movieSections.forEach(section => {
                    section.classList.remove('active');
                    section.style.display = 'none'; // Hide all sections
                    if (section.id === tabId) {
                        section.classList.add('active');
                        section.style.display = 'block'; // Show active section
                    }
                });

                // Update active tab variable
                activeTab = tabId;

                // Check if we're in search mode
                const container = document.getElementById(`${tabId}-movies`);
                const isSearchMode = container && container.hasAttribute('data-search-results');

                if (isSearchMode) {
                    console.log('In search mode, showing search results for tab:', tabId);
                    // Search results are already displayed, no need to load anything
                } else {
                    // Normal mode - load movies for this tab if not already loaded
                    const section = document.getElementById(tabId);
                    if (section && !section.hasAttribute('data-loaded')) {
                        console.log('Loading movies for tab:', tabId);

                        // Get current filter values
                        const genreSelect = document.getElementById('genre-filter');
                        const yearSelect = document.getElementById('year-filter');
                        const genreId = genreSelect ? genreSelect.value : '';
                        const year = yearSelect ? yearSelect.value : '';

                        // Load movies with current filters
                        loadMovies(tabId, 1, genreId, year);
                    } else {
                        console.log('Movies already loaded for tab:', tabId);
                    }
                }
            });
        });
    }

    // Private function to initialize filters
    function initFilters() {
        const genreSelect = document.getElementById('genre-filter');
        const yearSelect = document.getElementById('year-filter');
        const applyBtn = document.getElementById('apply-filters-btn');
        const clearBtn = document.getElementById('clear-filters');

        // Add event listener for genre filter (auto-apply)
        if (genreSelect) {
            genreSelect.addEventListener('change', function() {
                console.log('Genre filter changed:', this.value);
                applyFilters();
            });
        }

        // Add event listener for year filter (auto-apply)
        if (yearSelect) {
            yearSelect.addEventListener('change', function() {
                console.log('Year filter changed:', this.value);
                applyFilters();
            });
        }

        // Add event listener for apply button (if exists)
        if (applyBtn) {
            applyBtn.addEventListener('click', applyFilters);
        }

        // Add event listener for clear button
        if (clearBtn) {
            clearBtn.addEventListener('click', clearFilters);
        }

        // Add event listener for reset search button (in header)
        const resetSearchBtn = document.getElementById('reset-search');
        if (resetSearchBtn) {
            resetSearchBtn.addEventListener('click', resetSearch);
        }

        // Load genres and years
        loadGenres();
        loadYears();
    }

    // Private function to handle search
    function initSearch() {
        const searchForm = document.getElementById('search-form');
        const searchInput = document.getElementById('search-input');
        const searchButton = document.getElementById('search-button');

        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                e.preventDefault();
                performSearch();
            });
        }

        if (searchButton) {
            searchButton.addEventListener('click', performSearch);
        }

        if (searchInput) {
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    performSearch();
                }
            });
        }
    }

    // Private function to perform search
    function performSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput ? searchInput.value.trim() : '';

        if (!query) {
            alert('Masukkan kata kunci pencarian');
            return;
        }

        console.log('Performing search for:', query);

        // Show loading state
        const searchResultsSection = document.getElementById('search-results-section');
        const searchResults = document.getElementById('search-results');
        const searchResultsCount = document.getElementById('search-results-count');

        if (searchResultsSection) {
            searchResultsSection.style.display = 'block';
        }

        if (searchResults) {
            searchResults.innerHTML = '<div class="loading">Mencari film...</div>';
        }

        if (searchResultsCount) {
            searchResultsCount.textContent = 'Mencari...';
        }

        // Make API call
        fetch(getApiUrl('search?q=' + encodeURIComponent(query)))
            .then(response => response.json())
            .then(data => {
                console.log('Search results:', data);

                if (data.status === 'success') {
                    displaySearchResults(data);
                } else {
                    showSearchError(data.message || 'Terjadi kesalahan saat pencarian');
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                showSearchError('Terjadi kesalahan saat pencarian');
            });
    }

    // Private function to display search results
    function displaySearchResults(data) {
        const results = data.results || [];
        const totalResults = data.total_results || 0;
        const query = data.query || '';

        console.log(`Menampilkan ${results.length} hasil pencarian untuk query: "${query}"`);

        if (results.length === 0) {
            showSearchError(`Tidak ada hasil untuk "${query}"`);
            return;
        }

        // Simpan hasil pencarian ke global state
        currentMovies = results;
        activeTab = 'search'; // Set active tab ke search mode

        // Update semua tab dengan hasil pencarian
        const tabs = ['trending', 'newest', 'popular'];

        tabs.forEach(tabId => {
            const container = document.getElementById(`${tabId}-movies`);
            const pagination = document.getElementById(`${tabId}-pagination`);
            const tabButton = document.querySelector(`.tab-button[data-tab="${tabId}"]`);

            if (container) {
                // Kosongkan container
                container.innerHTML = '';

                // Urutkan hasil pencarian berdasarkan relevansi untuk setiap tab
                let sortedResults = [...results];

                // Untuk tab trending: urutkan berdasarkan trending_score = (vote_avg * vote_count)/1000 + recency_bonus
                // (harus konsisten dengan rumus _sort_trending di backend movie_service.py)
                if (tabId === 'trending') {
                    sortedResults.sort((a, b) => {
                        const scoreA = ((a.vote_average || 0) * (a.vote_count || 0)) / 1000;
                        const scoreB = ((b.vote_average || 0) * (b.vote_count || 0)) / 1000;
                        
                        // Tambahkan recency bonus untuk film rilis dalam 30 hari terakhir
                        const now = new Date();
                        const getRecencyBonus = (releaseDate) => {
                            if (!releaseDate) return 0;
                            try {
                                const rd = new Date(releaseDate);
                                const daysSince = Math.floor((now - rd) / (1000 * 60 * 60 * 24));
                                if (daysSince >= 0 && daysSince <= 30) {
                                    return (30 - daysSince) * 0.1;
                                }
                            } catch(e) {}
                            return 0;
                        };
                        
                        const finalA = scoreA + getRecencyBonus(a.release_date);
                        const finalB = scoreB + getRecencyBonus(b.release_date);
                        return finalB - finalA;
                    });
                }
                // Untuk tab newest: urutkan berdasarkan release_date (terbaru dulu)
                else if (tabId === 'newest') {
                    sortedResults.sort((a, b) => {
                        const dateA = new Date(a.release_date || '1900-01-01');
                        const dateB = new Date(b.release_date || '1900-01-01');
                        return dateB - dateA;
                    });
                }
                // Untuk tab popular: urutkan berdasarkan vote_average (rating tertinggi)
                else if (tabId === 'popular') {
                    sortedResults.sort((a, b) => (b.vote_average || 0) - (a.vote_average || 0));
                }

                // Tampilkan hasil pencarian
                const fragment = document.createDocumentFragment();
                sortedResults.forEach(movie => {
                    if (movie && movie.id) {
                        try {
                            const movieCard = createMovieCard(movie);
                            if (movieCard) {
                                fragment.appendChild(movieCard);
                            }
                        } catch (error) {
                            console.error('Gagal membuat kartu film:', error);
                        }
                    }
                });
                container.appendChild(fragment);

                // Kosongkan pagination untuk hasil pencarian
                if (pagination) {
                    pagination.innerHTML = '';
                }

                // JAGA NAMA TAB TETAP SAMA - Jangan ubah judul tab
                // Hanya tandai bahwa tab ini berisi hasil pencarian
                container.setAttribute('data-search-results', 'true');
                container.setAttribute('data-search-query', query);
            }
        });

        // Switch ke tab trending sebagai default
        App.switchTab('trending');

        // Tampilkan tombol reset pencarian
        const resetSearchBtn = document.getElementById('reset-search');
        if (resetSearchBtn) {
            resetSearchBtn.style.display = 'inline-block';
        }

        // Tambahkan tombol untuk kembali ke semua tab normal
        const trendingContainer = document.getElementById('trending-movies');
        if (trendingContainer && !trendingContainer.querySelector('.back-to-normal')) {
            const backButton = document.createElement('button');
            backButton.className = 'btn btn-secondary back-to-normal';
            backButton.innerHTML = '<i class="fas fa-arrow-left"></i> Kembali ke Normal';
            backButton.style.marginBottom = '20px';
            backButton.addEventListener('click', function() {
                // Reset ke mode normal
                resetToNormalMode();
            });

            // Sisipkan tombol kembali di awal container trending
            trendingContainer.insertBefore(backButton, trendingContainer.firstChild);
        }

        console.log(`Displayed ${results.length} search results in all tabs`);
    }

    // Private function to reset to normal mode
    function resetToNormalMode() {
        console.log('Resetting to normal mode...');

        // Reset active tab
        activeTab = 'trending';

        // Tab yang akan direset
        const tabs = ['trending', 'newest', 'popular'];

        // Hapus atribut pencarian dari semua container
        tabs.forEach(tabId => {
            const container = document.getElementById(`${tabId}-movies`);
            if (container) {
                container.removeAttribute('data-search-results');
                container.removeAttribute('data-search-query');
            }
        });

        // Sembunyikan tombol reset pencarian
        const resetSearchBtn = document.getElementById('reset-search');
        if (resetSearchBtn) {
            resetSearchBtn.style.display = 'none';
        }

        // Hapus tombol kembali
        const backButton = document.querySelector('.back-to-normal');
        if (backButton) {
            backButton.remove();
        }

        // Reset current movies
        currentMovies = [];

        // Reload semua tab dengan data normal dan filter yang ada
        const genreSelect = document.getElementById('genre-filter');
        const yearSelect = document.getElementById('year-filter');
        const genreId = genreSelect ? genreSelect.value : '';
        const year = yearSelect ? yearSelect.value : '';

        tabs.forEach(tabId => {
            loadMovies(tabId, 1, genreId, year);
        });
    }

    // Private function to show search error
    function showSearchError(message) {
        const searchResults = document.getElementById('search-results');
        const searchResultsCount = document.getElementById('search-results-count');

        if (searchResultsCount) {
            searchResultsCount.textContent = 'Error';
        }

        if (searchResults) {
            searchResults.innerHTML = `<div class="error-message">${message}</div>`;
        }
    }

    // Public API
    return {
        init: function() {
            console.log('Inisialisasi aplikasi...');

            // Initialize tabs
            initTabs();

            // Initialize filters
            initFilters();

            // Initialize search
            initSearch();

            // Load initial movies with stored filters
            const storedFilters = applyStoredFilters();
            const genreId = storedFilters ? storedFilters.genreId : '';
            const year = storedFilters ? storedFilters.year : '';
            loadMovies(activeTab, 1, genreId, year);
        },

        loadMovies: loadMovies,
        applyFilters: applyFilters,
        clearFilters: clearFilters,
        showMovieDetails: showMovieDetails,
        performSearch: performSearch,
        switchTab: function(tabId) {
            console.log('Switching to tab:', tabId);
            const tabButton = document.querySelector(`.tab-button[data-tab="${tabId}"]`);
            if (tabButton) {
                tabButton.click();
            } else {
                console.error('Tab button not found for:', tabId);
            }
        }
    };
})();

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});
