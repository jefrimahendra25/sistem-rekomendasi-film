"""
Utility functions for the movie recommendation API
"""
import os
import logging
from datetime import datetime
from functools import wraps
from flask import jsonify
import traceback
import pandas as pd

logger = logging.getLogger(__name__)

def handle_api_errors(f):
    """Decorator untuk menangani error di API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as ve:
            logger.warning(f"Parameter tidak valid: {str(ve)}")
            return jsonify({'status': 'error', 'message': 'Parameter tidak valid'}), 400
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'status': 'error', 'message': 'Terjadi kesalahan server'}), 500
    return decorated_function

def validate_pagination_params(page, items_per_page=20):
    """Validasi parameter paginasi"""
    try:
        page = int(page) if page else 1
        if page < 1:
            page = 1
        return page, items_per_page
    except (ValueError, TypeError):
        return 1, items_per_page

def validate_movie_filters(genre_id='', year=''):
    """Validasi dan normalisasi filter film"""
    # Validasi genre
    if genre_id and str(genre_id).strip():
        try:
            genre_id = str(int(genre_id))  # Pastikan genre_id adalah string angka
        except (ValueError, TypeError):
            genre_id = ''
    else:
        genre_id = ''

    # Validasi tahun
    if year and str(year).strip() and str(year).isdigit():
        year_int = int(year)
        if 1900 <= year_int <= datetime.now().year + 5:  # Tahun masuk akal
            year = str(year_int)
        else:
            year = ''
    else:
        year = ''

    return genre_id, year

def clean_poster_path(path):
    """
    Membersihkan dan memvalidasi path poster.
    Mengembalikan URL poster yang valid atau path default jika tidak valid.
    """
    default_poster = '/static/images/no-poster.svg'

    try:
        # Convert to string first
        path = str(path).strip() if path is not None else ''

        # Handle missing or invalid paths
        if not path or path.lower() in ['nan', 'none', 'null', ''] or pd.isna(path):
            return default_poster

        # Check for 'nan' in any case or position
        if 'nan' in path.lower() or 'w500nan' in path.lower() or 'null' in path.lower():
            return default_poster

        # Check if path is just 'nan' (case insensitive)
        if path.lower() == 'nan':
            return default_poster

        # Remove any query parameters and fragments
        path = path.split('?')[0].split('#')[0]

        # Handle empty path after cleaning
        if not path:
            return default_poster

        # Handle relative paths (start with /)
        if path.startswith('/'):
            return f"https://image.tmdb.org/t/p/w500{path}"

        # Handle full URLs
        if path.startswith(('http://', 'https://')):
            # Validate TMDB image URL
            if 'image.tmdb.org' in path:
                # Ensure proper TMDB URL format
                if '/t/p/' not in path:
                    # If it's a TMDB URL but missing the size, add default size
                    base_url = path.split('image.tmdb.org')[0] + 'image.tmdb.org'
                    path = f"{base_url}/t/p/w500{path.split('image.tmdb.org')[-1].split('/')[-1]}"
                return path
            return default_poster

        # Handle just the filename
        if path.startswith('/'):
            # Remove any duplicate /t/p/w500/ if present
            clean_path = path.replace('/t/p/w500/', '').lstrip('/')
            if not clean_path or 'nan' in clean_path.lower():
                return default_poster

            # Ensure the path has a valid extension
            if not any(clean_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                return default_poster

            return f"https://image.tmdb.org/t/p/w500/{clean_path}"

        # Handle paths without leading slash (should be very rare)
        clean_path = path.lstrip('/')
        if not clean_path or 'nan' in clean_path.lower():
            return default_poster

        # Ensure the path has a valid extension
        if not any(clean_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            return default_poster

        return f"https://image.tmdb.org/t/p/w500/{clean_path}"

    except Exception as e:
        logger.error(f"Error processing poster path '{path}': {str(e)}")
        return default_poster

def validate_movie_data(movie):
    """Validasi dan bersihkan data film"""
    try:
        # Validasi ID
        if 'id' not in movie or not str(movie['id']).strip():
            return None

        # Validasi judul
        if 'title' not in movie or not str(movie.get('title', '')).strip():
            movie['title'] = f"Film {movie['id']}"

        # Validasi dan format rating
        if 'vote_average' in movie:
            try:
                rating = float(str(movie['vote_average']).replace(',', '.').strip())
                movie['vote_average'] = round(max(0, min(10, rating)), 1)
            except (ValueError, TypeError):
                movie['vote_average'] = 0.0

        # Validasi dan format vote_count
        if 'vote_count' in movie:
            try:
                count = int(float(str(movie['vote_count']).replace(',', '.').strip()))
                movie['vote_count'] = max(0, count)
            except (ValueError, TypeError):
                movie['vote_count'] = 0

        # Validasi poster_path
        if 'poster_path' in movie:
            movie['poster_path'] = clean_poster_path(movie['poster_path'])

        # Validasi release_date
        if 'release_date' in movie:
            if not movie['release_date'] or str(movie['release_date']).lower() in ['nan', 'none']:
                movie['release_date'] = '1970-01-01'

        # Validasi genres
        if 'genres' not in movie or not movie['genres']:
            movie['genres'] = []
        elif isinstance(movie['genres'], str):
            # Jika genres adalah string, coba parse sebagai JSON atau split by comma
            try:
                import json
                movie['genres'] = json.loads(movie['genres'])
            except (json.JSONDecodeError, TypeError):
                movie['genres'] = [g.strip() for g in movie['genres'].split(',') if g.strip()]

        return movie

    except Exception as e:
        logger.error(f"Error validating movie data: {str(e)}")
        return None

def paginate_movies(movies, page=1, items_per_page=20, show_all=False):
    """Helper function untuk pagination"""
    if not movies:
        return [], page, 1, 0

    total_movies = len(movies)
    total_pages = max(1, (total_movies + items_per_page - 1) // items_per_page)

    # Validasi page. Jika page melebihi total halaman, tidak ada hasil.
    if page > total_pages:
        return [], page, total_pages, total_movies

    if show_all:
        return movies, page, total_pages, total_movies

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_movies = movies[start_idx:end_idx]

    return paginated_movies, page, total_pages, total_movies

def create_api_response(status='success', data=None, message=None, **kwargs):
    """Helper untuk membuat response API yang konsisten"""
    response = {'status': status}

    if data is not None:
        response['data'] = data

    if message:
        response['message'] = message

    # Tambahkan kwargs lainnya
    response.update(kwargs)

    return jsonify(response)

def get_data_file_path():
    """Mendapatkan path ke file data CSV"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'Data')
    return os.path.join(data_dir, 'film_indonesia_terfilter.csv')
