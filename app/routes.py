from flask import Flask, jsonify, Blueprint, request, current_app
from flask_cors import CORS, cross_origin
from flask_limiter import Limiter
from flask_caching import Cache
import logging
import os
import traceback
from datetime import datetime
from app.utils import handle_api_errors, validate_pagination_params, validate_movie_filters, paginate_movies, create_api_response
from app.movie_service import movie_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Inisialisasi Blueprint dengan prefix /api
main = Blueprint('api', __name__, url_prefix='/api')

# Konfigurasi CORS
cors = CORS(main, resources={
    r"/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(','),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Disposition"]
    }
})


@main.route('/', methods=['GET'])
@handle_api_errors
def index():
    """Endpoint utama untuk menampilkan dokumentasi API"""
    return create_api_response(
        message='Selamat datang di API Rekomendasi Film',
        endpoints={
            'popular_movies': '/api/movies?type=popular',
            'trending_movies': '/api/movies?type=trending',
            'newest_movies': '/api/movies?type=newest',
            'search': '/api/search?q=query',
            'movie_details': '/api/movie/<int:movie_id>'
        }
    )


# Specific movie type endpoints for better compatibility
@main.route('/movies/trending', methods=['GET'])
@cross_origin()
@handle_api_errors
def get_trending_movies():
    return get_movies('trending')


@main.route('/movies/newest', methods=['GET'])
@cross_origin()
@handle_api_errors
def get_newest_movies():
    return get_movies('newest')


@main.route('/movies/popular', methods=['GET'])
@cross_origin()
@handle_api_errors
def get_popular_movies():
    return get_movies('popular')


@main.route('/movies', methods=['GET', 'OPTIONS'])
@cross_origin()
@handle_api_errors
def get_movies(movie_type=None):
    """Endpoint untuk mendapatkan daftar film dengan paginasi"""

    # movie_type bisa datang dari path helper (popular/newest/trending) atau querystring (?type=...)
    movie_type = movie_type or request.args.get('type', 'trending')
    page = request.args.get('page', 1)
    show_all = request.args.get('show_all', 'false').lower() == 'true'

    genre_id = request.args.get('genre', '') or request.args.get('genre_id', '')
    year = request.args.get('year', '')
    limit = request.args.get('limit', 20)

    page, _ = validate_pagination_params(page)
    genre_id, year = validate_movie_filters(genre_id, year)

    try:
        limit = int(limit)
        limit = max(1, min(limit, 100))
    except (ValueError, TypeError):
        limit = 20

    logger.info(f"Getting movies: type={movie_type}, genre={genre_id}, year={year}, page={page}")

    # Disable caching in test environment to avoid serialization issues with pytest_flask responses.
    if os.getenv('PYTEST_CURRENT_TEST'):
        cache = None
    else:
        cache = current_app.cache if hasattr(current_app, 'cache') else None

    cache_key = f"movies_{movie_type}_{genre_id}_{year}_{page}_{show_all}_{limit}"

    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {cache_key}")
            return cached_result

    movies_data = movie_service.load_movies()
    if not isinstance(movies_data, list):
        return create_api_response(status='error', message='Invalid data format'), 500

    filtered_movies = movie_service.filter_movies(movies_data, genre_id, year)
    sorted_movies = movie_service.sort_movies(filtered_movies, movie_type)

    paginated_movies, page, total_pages, total_movies = paginate_movies(
        sorted_movies, page, items_per_page=limit, show_all=show_all
    )

    logger.info(f"Returning {len(paginated_movies)} movies (page {page}/{total_pages})")

    result = create_api_response(
        movies=paginated_movies,
        page=page,
        total_pages=total_pages,
        total_movies=total_movies,
        items_per_page=limit
    )

    if cache:
        cache.set(cache_key, result, timeout=300)

    return result


@main.route('/movie/<int:movie_id>', methods=['GET'])
@cross_origin()
@handle_api_errors
def get_movie_details(movie_id):
    logger.info(f"Getting movie details for ID: {movie_id}")

    movies_data = movie_service.load_movies()
    movie = movie_service.get_movie_by_id(movie_id, movies_data)

    if not movie:
        return create_api_response(status='error', message=f'Movie with ID {movie_id} not found'), 404

    # Pastikan id selalu numerik (untuk konsistensi response API dan test)
    try:
        if movie.get('id') is not None:
            movie['id'] = int(float(str(movie['id']).replace(',', '')))
    except Exception:
        pass

    logger.info(f"Successfully retrieved movie details: {movie.get('title')}")



    return create_api_response(movie=movie)


@main.route('/movie/<movie_id>/recommendations', methods=['GET'])
@cross_origin()
@handle_api_errors
def get_movie_recommendations(movie_id):

    logger.info(f"Getting recommendations for movie ID: {movie_id}")

    top_n = request.args.get('top_n', 10, type=int)
    top_n = min(max(top_n, 1), 20)

    movies_data = movie_service.load_movies()
    movie = movie_service.get_movie_by_id(movie_id, movies_data)

    if not movie:
        return create_api_response(status='error', message=f'Movie with ID {movie_id} not found'), 404

    recommendations = movie_service.recommend_movies(movie_id, movies_data, top_n=top_n)

    logger.info(
        f"Successfully retrieved {len(recommendations)} recommendations for movie: {movie.get('title')}"
    )

    return create_api_response(
        movie=movie,
        recommendations=recommendations,
        total_recommendations=len(recommendations)
    )


@main.route('/search', methods=['GET'])
@cross_origin()
@handle_api_errors
def search_movies():
    try:
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1)
        show_all = request.args.get('show_all', 'false').lower() == 'true'

        logger.info(f"Search request received - query: '{query}', page: {page}, show_all: {show_all}")

        if not query:
            logger.warning("Search request missing required 'q' parameter")
            return create_api_response(
                status='error',
                message='Query parameter (q) is required',
                query=query,
                results=[],
                total_results=0
            ), 400

        try:
            page, _ = validate_pagination_params(page)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid page parameter: {e}")
            return create_api_response(
                status='error',
                message='Invalid page parameter',
                query=query,
                results=[],
                total_results=0
            ), 400

        logger.info(f"Searching movies: query='{query}', page={page}, show_all={show_all}")

        if os.getenv('PYTEST_CURRENT_TEST'):
            cache = None
        else:
            cache = current_app.cache if hasattr(current_app, 'cache') else None

        cache_key = f"search_{query}_{page}_{show_all}"
        if cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for search: {cache_key}")
                return cached_result

        movies_data = movie_service.load_movies()
        logger.info(f"Loaded {len(movies_data)} movies for search")

        search_results = movie_service.search_movies(query, movies_data, min_results=20)
        logger.info(f"Search completed, found {len(search_results)} results")

        paginated_results, page, total_pages, total_results = paginate_movies(
            search_results, page, show_all=show_all
        )

        logger.info(f"Returning {len(paginated_results)} search results (page {page}/{total_pages})")

        result = create_api_response(
            status='success',
            query=query,
            results=paginated_results,
            page=page,
            total_pages=total_pages,
            total_results=total_results,
            items_per_page=20
        )

        if cache:
            cache.set(cache_key, result, timeout=600)

        return result

    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        return create_api_response(
            status='error',
            message='Terjadi kesalahan saat melakukan pencarian',
            error_details=str(e),
            query=request.args.get('q', '')
        ), 500


@main.route('/genres', methods=['GET'])
@cross_origin()
@handle_api_errors
def get_genres():
    logger.info("Getting available genres")
    try:
        movies_data = movie_service.load_movies()
        available_genres = movie_service.get_genres(movies_data)

        formatted_genres = []
        for genre in available_genres:
            if isinstance(genre, dict):
                formatted_genres.append({
                    'id': int(genre.get('id', 0)),
                    'name': str(genre.get('name', '')),
                    'count': int(genre.get('count', 0))
                })

        logger.info(f"Successfully retrieved {len(formatted_genres)} genres")

        return {
            'status': 'success',
            'genres': formatted_genres,
            'total': len(formatted_genres)
        }
    except Exception as e:
        logger.error(f"Error in get_genres: {str(e)}")
        return {
            'status': 'error',
            'message': 'Gagal memuat daftar genre',
            'error': str(e)
        }, 500


@main.route('/welcome', methods=['GET'])
@cross_origin()
@handle_api_errors
def welcome():
    logger.info(f"Request received: {request.method} {request.path}")
    return create_api_response(message='Selamat datang di API Rekomendasi Film!')


@main.route('/countries', methods=['GET'])
@cross_origin()
def get_countries():
    try:
        country_map = {
            'ID': 'Indonesia',
            'US': 'Amerika Serikat',
            'GB': 'Britania Raya',
            'FR': 'Prancis',
            'DE': 'Jerman',
            'IT': 'Italia',
            'JP': 'Jepang',
            'KR': 'Korea Selatan',
            'CN': 'China',
            'IN': 'India',
            'AU': 'Australia',
            'CA': 'Kanada',
            'BR': 'Brasil',
            'MX': 'Meksiko',
            'ES': 'Spanyol',
            'RU': 'Rusia',
            'TH': 'Thailand',
            'MY': 'Malaysia',
            'SG': 'Singapura',
            'PH': 'Filipina',
            'VN': 'Vietnam',
            'HK': 'Hong Kong',
            'TW': 'Taiwan',
            'NL': 'Belanda',
            'SE': 'Swedia',
            'NO': 'Norwegia',
            'DK': 'Denmark',
            'FI': 'Finlandia',
            'PL': 'Polandia',
            'CZ': 'Republik Ceko',
            'HU': 'Hungaria',
            'TR': 'Turki',
            'ZA': 'Afrika Selatan',
            'AR': 'Argentina',
            'CL': 'Chile',
            'CO': 'Kolombia',
            'PE': 'Peru',
            'VE': 'Venezuela',
            'EG': 'Mesir',
            'MA': 'Maroko',
            'NG': 'Nigeria',
            'KE': 'Kenya',
            'GH': 'Ghana',
            'AE': 'Uni Emirat Arab',
            'SA': 'Arab Saudi',
            'IL': 'Israel',
            'IR': 'Iran',
            'IQ': 'Irak',
            'JO': 'Yordania',
            'LB': 'Lebanon',
            'SY': 'Suriah',
            'PK': 'Pakistan',
            'BD': 'Bangladesh',
            'LK': 'Sri Lanka',
            'NP': 'Nepal',
            'MM': 'Myanmar',
            'KH': 'Kamboja',
            'LA': 'Laos',
            'KZ': 'Kazakhstan',
            'UZ': 'Uzbekistan',
            'KG': 'Kyrgyzstan',
            'TJ': 'Tajikistan',
            'TM': 'Turkmenistan',
            'AZ': 'Azerbaijan',
            'GE': 'Georgia',
            'AM': 'Armenia',
            'BY': 'Belarus',
            'UA': 'Ukraina',
            'RO': 'Rumania',
            'BG': 'Bulgaria',
            'HR': 'Kroasia',
            'SI': 'Slovenia',
            'BA': 'Bosnia dan Herzegovina',
            'ME': 'Montenegro',
            'MK': 'Makedonia Utara',
            'AL': 'Albania',
            'GR': 'Yunani',
            'PT': 'Portugal',
            'CH': 'Swiss',
            'AT': 'Austria',
            'BE': 'Belgia',
            'LU': 'Luksemburg',
            'IE': 'Irlandia',
            'IS': 'Islandia',
            'NZ': 'Selandia Baru',
            'FJ': 'Fiji',
            'PG': 'Papua Nugini',
            'SB': 'Solomon Islands',
            'VU': 'Vanuatu',
            'NC': 'Kaledonia Baru',
            'PF': 'Polinesia Prancis',
            'WS': 'Samoa',
            'TO': 'Tonga',
            'TV': 'Tuvalu',
            'KI': 'Kiribati',
            'MH': 'Marshall Islands',
            'FM': 'Mikronesia',
            'PW': 'Palau',
            'NR': 'Nauru'
        }

        countries = [{'code': code, 'name': name} for code, name in sorted(country_map.items(), key=lambda x: x[1])]

        return jsonify({
            'status': 'success',
            'count': len(countries),
            'countries': countries
        })
    except Exception as e:
        logger.error(f"Error in get_countries: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500












@main.route('/debug/movie_stats', methods=['GET'])
@cross_origin()
def debug_movie_stats():
    """Endpoint untuk memeriksa statistik data film"""
    try:
        movies = movie_service.load_movies()

        if not isinstance(movies, list):
            return jsonify({
                'status': 'error',
                'message': 'Gagal memuat data film',
                'details': str(movies)
            }), 500

        genre_count = {}
        for movie in movies:
            for genre in movie.get('genres', []):
                if isinstance(genre, dict):
                    genre_name = genre.get('name') or genre.get('id') or str(genre)
                else:
                    genre_name = str(genre)
                genre_count[genre_name] = genre_count.get(genre_name, 0) + 1

        year_count = {}
        for movie in movies:
            try:
                year = movie.get('release_date', '').split('-')[0]
                if year and year.isdigit():
                    year_count[year] = year_count.get(year, 0) + 1
            except Exception:
                pass

        ratings = [float(m.get('vote_average', 0)) for m in movies if m.get('vote_average') is not None]

        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'Data',
            'film_indonesia_terfilter.csv'
        )

        return jsonify({
            'status': 'success',
            'total_movies': len(movies),
            'data_source': data_path,
            'file_exists': os.path.exists(data_path),
            'file_size': f"{os.path.getsize(data_path) / (1024 * 1024):.2f} MB" if os.path.exists(data_path) else 'N/A',
            'genres': {
                'count': len(genre_count),
                'list': [{'name': k, 'count': v} for k, v in sorted(genre_count.items(), key=lambda x: x[1], reverse=True)]
            },
            'years': {
                'count': len(year_count),
                'range': {
                    'min': min(year_count.keys()) if year_count else 'N/A',
                    'max': max(year_count.keys()) if year_count else 'N/A'
                },
                'distribution': [{'year': k, 'count': v} for k, v in sorted(year_count.items())]
            },
            'ratings': {
                'min': min(ratings) if ratings else 0,
                'max': max(ratings) if ratings else 0,
                'average': sum(ratings) / len(ratings) if ratings else 0,
                'count': len(ratings)
            },
            'sample_movies': [
                {k: v for k, v in m.items() if k != 'original_data'}
                for m in movies[:3]
            ] if len(movies) > 0 else []
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

