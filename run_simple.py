"""
Simple runner untuk aplikasi FilmKu tanpa dependencies kompleks
"""
import os
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

def create_simple_app():
    """Create simple Flask app"""
    app = Flask(
        __name__,
        static_folder='app/static',
        static_url_path='/static',
        template_folder='app/templates'
    )
    
    # Basic configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-yang-sangat-rahasia'),
        DEBUG=os.getenv('FLASK_DEBUG', 'True') == 'True',
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024
    )
    
    # Setup CORS
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(',')
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    logger = logging.getLogger(__name__)
    
    # Import movie service (original CSV-based)
    try:
        from app.movie_service import movie_service
        logger.info("Movie service loaded successfully")
    except ImportError as e:
        logger.error(f"Failed to import movie service: {e}")
        movie_service = None
    
    # Routes
    @app.route('/')
    def index():
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f'Error rendering index.html: {str(e)}')
            return f"Error: {str(e)}", 500
    
    @app.route('/api/welcome')
    def api_welcome():
        return jsonify({
            'status': 'success',
            'message': 'Selamat datang di FilmKu API!',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'movies': '/api/movies',
                'search': '/api/search',
                'genres': '/api/genres',
                'health': '/health'
            }
        })
    
    @app.route('/api/movies')
    def get_movies():
        if not movie_service:
            return jsonify({
                'status': 'error',
                'message': 'Movie service not available'
            }), 500
        
        try:
            movie_type = request.args.get('type', 'trending')
            page = int(request.args.get('page', 1))
            show_all = request.args.get('show_all', 'false').lower() == 'true'
            genre_id = request.args.get('genre', '')
            year = request.args.get('year', '')
            
            logger.info(f"Getting movies: type={movie_type}, page={page}")
            
            # Load movies
            movies_data = movie_service.load_movies()
            if not isinstance(movies_data, list):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid data format'
                }), 500
            
            # Apply filters
            filtered_movies = movie_service.filter_movies(movies_data, genre_id, year)
            
            # Sort movies
            sorted_movies = movie_service.sort_movies(filtered_movies, movie_type)
            
            # Paginate
            if show_all:
                movies = sorted_movies
                total_movies = len(movies)
                total_pages = 1
            else:
                per_page = 20
                start = (page - 1) * per_page
                end = start + per_page
                movies = sorted_movies[start:end]
                total_movies = len(sorted_movies)
                total_pages = (total_movies + per_page - 1) // per_page
            
            return jsonify({
                'status': 'success',
                'movies': movies,
                'page': page,
                'total_pages': total_pages,
                'total_movies': total_movies,
                'items_per_page': 20
            })
            
        except Exception as e:
            logger.error(f"Error getting movies: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Terjadi kesalahan saat mengambil data film'
            }), 500
    
    @app.route('/api/search')
    def search_movies():
        if not movie_service:
            return jsonify({
                'status': 'error',
                'message': 'Movie service not available'
            }), 500
        
        try:
            query = request.args.get('q', '').strip()
            page = int(request.args.get('page', 1))
            show_all = request.args.get('show_all', 'false').lower() == 'true'
            
            if not query:
                return jsonify({
                    'status': 'error',
                    'message': 'Query parameter (q) is required',
                    'query': query,
                    'results': [],
                    'total_results': 0
                }), 400
            
            logger.info(f"Searching movies: query='{query}', page={page}")
            
            # Load and search
            movies_data = movie_service.load_movies()
            search_results = movie_service.search_movies(query, movies_data)
            
            # Paginate
            if show_all:
                results = search_results
                total_results = len(results)
                total_pages = 1
            else:
                per_page = 20
                start = (page - 1) * per_page
                end = start + per_page
                results = search_results[start:end]
                total_results = len(search_results)
                total_pages = (total_results + per_page - 1) // per_page
            
            return jsonify({
                'status': 'success',
                'query': query,
                'results': results,
                'page': page,
                'total_pages': total_pages,
                'total_results': total_results,
                'items_per_page': 20
            })
            
        except Exception as e:
            logger.error(f"Error searching movies: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Terjadi kesalahan saat melakukan pencarian',
                'query': query
            }), 500
    
    @app.route('/api/movie/<int:movie_id>')
    def get_movie_details(movie_id):
        if not movie_service:
            return jsonify({
                'status': 'error',
                'message': 'Movie service not available'
            }), 500
        
        try:
            logger.info(f"Getting movie details for ID: {movie_id}")
            
            movies_data = movie_service.load_movies()
            movie = movie_service.get_movie_by_id(movie_id, movies_data)
            
            if not movie:
                return jsonify({
                    'status': 'error',
                    'message': f'Movie dengan ID {movie_id} tidak ditemukan'
                }), 404
            
            return jsonify({
                'status': 'success',
                'movie': movie
            })
            
        except Exception as e:
            logger.error(f"Error getting movie details: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Terjadi kesalahan saat mengambil detail film'
            }), 500
    
    @app.route('/api/genres')
    def get_genres():
        if not movie_service:
            return jsonify({
                'status': 'error',
                'message': 'Movie service not available'
            }), 500
        
        try:
            movies_data = movie_service.load_movies()
            genres = movie_service.get_genres(movies_data)
            
            return jsonify({
                'status': 'success',
                'genres': genres,
                'total': len(genres)
            })
            
        except Exception as e:
            logger.error(f"Error getting genres: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Terjadi kesalahan saat mengambil data genre'
            }), 500
    
    @app.route('/health')
    def health_check():
        try:
            total_movies = 0
            if movie_service:
                movies_data = movie_service.load_movies()
                total_movies = len(movies_data) if isinstance(movies_data, list) else 0
            
            return jsonify({
                'status': 'healthy',
                'total_movies': total_movies,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0-simple',
                'cache_status': 'disabled'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': 'Halaman tidak ditemukan',
            'path': request.path
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Terjadi kesalahan internal server',
            'path': request.path
        }), 500
    
    logger.info("Simple application initialized successfully")
    return app

if __name__ == '__main__':
    app = create_simple_app()
    port = int(os.getenv('PORT', 5002))
    print(f"🚀 FilmKu API starting on http://localhost:{port}")
    print("📚 API Documentation: http://localhost:{port}/api/welcome")
    print("🏥 Health Check: http://localhost:{port}/health")
    app.run(host='0.0.0.0', port=port, debug=True)
