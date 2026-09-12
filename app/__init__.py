import os
from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_cors import CORS
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta, datetime
import secrets

# Initialize extensions
db = SQLAlchemy()

def setup_logging(app):
    """Mengkonfigurasi logging untuk aplikasi."""
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        # Prevent duplicate handlers across multiple app instances (pytest)
        if not any(
            isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', '') == file_handler.baseFilename
            for h in app.logger.handlers
        ):
            app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplikasi dimulai')

def load_environment():
    """Memuat variabel environment dari file .env."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        logging.warning("File .env tidak ditemukan. Pastikan file .env sudah dibuat.")

def create_app():
    """Membuat dan mengkonfigurasi instance Flask."""
    # Setup logging dasar
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load environment variables
    load_environment()

    # Inisialisasi Flask
    app = Flask(
        __name__,
        static_folder='static',
        static_url_path='/static',
        template_folder='templates'
    )

    # Generate secure secret key if not provided
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key or secret_key == 'your_super_secret_key_change_this_in_production':
        if os.getenv('FLASK_ENV') == 'production':
            logger.warning(
                "Using auto-generated secret key in production! Please set SECRET_KEY environment variable."
            )
        secret_key = secrets.token_hex(32)

    # Konfigurasi CORS yang lebih aman
    allowed_origins = os.getenv(
        'ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000'
    ).split(',')
    cors_config = {
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "expose_headers": ["Content-Disposition"]
        }
    }

    CORS(app, resources=cors_config)

    # Konfigurasi Dasar
    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(seconds=int(os.getenv('SESSION_TIMEOUT', 3600))),
        CORS_HEADERS='Content-Type,Authorization',
        CORS_ORIGINS=allowed_origins,
        TMDB_API_KEY=os.getenv('TMDB_API_KEY', ''),
        DEBUG=os.getenv('FLASK_DEBUG', 'True') == 'True',
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload
        # IMPORTANT: harus ter-set sebelum db.init_app(app)
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///movies.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Setup caching
    cache_config = {
        'CACHE_TYPE': os.getenv('CACHE_TYPE', 'simple'),
        'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    }

    # Use Redis if available
    redis_url = os.getenv('REDIS_URL')
    if redis_url and redis_url != 'redis://localhost:6379/0':
        cache_config.update({
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': redis_url
        })

    cache = Cache(app, config=cache_config)

    # Initialize database (setelah SQLALCHEMY_DATABASE_URI ter-set)
    db.init_app(app)

    # Setup Sentry if configured
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn and sentry_dsn != 'your_sentry_dsn_here':
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            logger.info("Sentry monitoring initialized")
        except ImportError:
            logger.warning("Sentry SDK not installed, monitoring disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    # Route untuk static files dengan CORS
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        response = send_from_directory(app.static_folder, filename)
        response.headers.add('Access-Control-Allow-Origin', ', '.join(allowed_origins))
        response.headers.add('Cache-Control', 'public, max-age=3600')
        return response

    # Route untuk file gambar dengan CORS
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        response = send_from_directory(os.path.join(app.static_folder, 'images'), filename)
        response.headers.add('Access-Control-Allow-Origin', ', '.join(allowed_origins))
        response.headers.add('Cache-Control', 'public, max-age=3600')
        return response

    # Tambahkan header CORS untuk semua respons
    @app.after_request
    def add_cors_headers(response):
        if not request.path.startswith(('/static/', '/images/')):
            response.headers.add('Access-Control-Allow-Origin', ', '.join(allowed_origins))
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            response.headers.add('Access-Control-Max-Age', '3600')
        return response

    # Setup logging lanjutan
    setup_logging(app)

    # Route untuk halaman utama (didefinisikan sebelum blueprint)
    @app.route('/')
    def index():
        try:
            return render_template('index.html')
        except Exception as e:
            app.logger.error(f'Error rendering index.html: {str(e)}')
            return '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FilmKu - Rekomendasi Film Indonesia</title>
</head>
<body>
    <h1>🎬 FilmKu API</h1>
    <p>Server Berjalan.</p>
</body>
</html>
            ''', 200

    # Route untuk favicon.ico
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )

    # Import dan registrasi blueprint
    from . import routes
    from . import docs
    app.register_blueprint(routes.main)
    app.register_blueprint(docs.docs_bp, url_prefix='/docs')

    # Root alias route untuk /countries agar endpoint tersedia di kedua path
    @app.route('/countries', methods=['GET'])
    def countries_root():
        return routes.get_countries()

    # Root alias route untuk debug movie stats agar endpoint /debug/movie_stats tersedia
    @app.route('/debug/movie_stats', methods=['GET'])
    def debug_movie_stats_root():
        return routes.debug_movie_stats()

    # Initialize Swagger documentation
    try:
        from .swagger import init_swagger
        init_swagger(app)
    except ImportError:
        logger.warning("Flask-RESTX not installed, Swagger documentation disabled")

    # Store cache in app context for use in routes
    app.cache = cache
    app.db = db

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': 'Halaman tidak ditemukan',
            'path': request.path
        }), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'status': 'error',
            'code': 429,
            'message': 'Terlalu banyak permintaan, coba lagi nanti',
            'retry_after': str(e.retry_after) if hasattr(e, 'retry_after') else '60'
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Terjadi kesalahan internal server',
            'path': request.path
        }), 500

    # Health handler: deterministik dan tidak mungkin menjadi 'null'
    @app.route('/health', methods=['GET'])
    def health_check_root():
        return (
            '{"status":"healthy","total_movies":0,'
            f'"timestamp":"{datetime.now().isoformat()}",'
            '"version":"1.0.0"}'
        ), 200, {'Content-Type': 'application/json; charset=utf-8'}


    logger.info("Application initialized successfully")
    return app

