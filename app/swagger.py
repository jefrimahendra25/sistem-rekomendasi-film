"""
Swagger/OpenAPI documentation configuration
"""
from flask import Blueprint, jsonify
from flask_restx import Api, Resource, fields, Namespace

# Create API documentation
authorizations = {
    'apiKey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

# Create Swagger API instance
swagger_api = Api(
    version='1.0',
    title='FilmKu API',
    description='API untuk aplikasi rekomendasi film Indonesia',
    doc='/docs/',
    contact='FilmKu Team',
    contact_email='support@filmku.com',
    authorizations=authorizations
)

# Define models for documentation
movie_model = swagger_api.model('Movie', {
    'id': fields.Integer(description='ID unik film'),
    'title': fields.String(description='Judul film'),
    'original_title': fields.String(description='Judul asli film'),
    'overview': fields.String(description='Sinopsis film'),
    'release_date': fields.Date(description='Tanggal rilis'),
    'popularity': fields.Float(description='Skor popularitas'),
    'vote_average': fields.Float(description='Rating rata-rata'),
    'vote_count': fields.Integer(description='Jumlah vote'),
    'poster_path': fields.String(description='Path poster film'),
    'backdrop_path': fields.String(description='Path backdrop film'),
    'original_language': fields.String(description='Bahasa asli'),
    'runtime': fields.Integer(description='Durasi film (menit)'),
    'director': fields.String(description='Sutradara'),
    'genres': fields.List(fields.Raw(), description='Daftar genre'),
    'production_countries': fields.List(fields.Raw(), description='Daftar negara produksi')
})

genre_model = swagger_api.model('Genre', {
    'id': fields.Integer(description='ID genre'),
    'name': fields.String(description='Nama genre'),
    'count': fields.Integer(description='Jumlah film dalam genre ini')
})

recommendation_model = swagger_api.model('Recommendation', {
    'id': fields.Integer(description='ID film yang direkomendasikan'),
    'title': fields.String(description='Judul film'),
    'similarity_score': fields.Float(description='Skor kemiripan'),
    'recommendation_type': fields.String(description='Tipe rekomendasi')
})

error_model = swagger_api.model('Error', {
    'status': fields.String(description='Status error'),
    'message': fields.String(description='Pesan error'),
    'code': fields.Integer(description='HTTP status code')
})

pagination_model = swagger_api.model('Pagination', {
    'page': fields.Integer(description='Nomor halaman saat ini'),
    'total_pages': fields.Integer(description='Total halaman'),
    'total_movies': fields.Integer(description='Total film'),
    'items_per_page': fields.Integer(description='Item per halaman')
})

# Create namespaces
movies_ns = Namespace('movies', description='Operasi film')
search_ns = Namespace('search', description='Pencarian film')
genres_ns = Namespace('genres', description='Genre film')
recommendations_ns = Namespace('recommendations', description='Rekomendasi film')

# Add namespaces to API
swagger_api.add_namespace(movies_ns)
swagger_api.add_namespace(search_ns)
swagger_api.add_namespace(genres_ns)
swagger_api.add_namespace(recommendations_ns)

# Movie endpoints documentation
@movies_ns.route('/trending')
class TrendingMovies(Resource):
    @swagger_api.doc('get_trending_movies')
    @swagger_api.marshal_list_with(movie_model)
    @swagger_api.param('page', 'Nomor halaman', type='integer', default=1)
    @swagger_api.param('genre', 'Filter genre', type='string')
    @swagger_api.param('year', 'Filter tahun', type='string')
    @swagger_api.param('show_all', 'Tampilkan semua film', type='boolean', default=False)
    @swagger_api.response(200, 'Success', pagination_model)
    @swagger_api.response(400, 'Bad Request', error_model)
    @swagger_api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """Dapatkan daftar film trending"""
        pass

@movies_ns.route('/popular')
class PopularMovies(Resource):
    @swagger_api.doc('get_popular_movies')
    @swagger_api.marshal_list_with(movie_model)
    @swagger_api.param('page', 'Nomor halaman', type='integer', default=1)
    @swagger_api.param('genre', 'Filter genre', type='string')
    @swagger_api.param('year', 'Filter tahun', type='string')
    @swagger_api.param('show_all', 'Tampilkan semua film', type='boolean', default=False)
    @swagger_api.response(200, 'Success', pagination_model)
    @swagger_api.response(400, 'Bad Request', error_model)
    @swagger_api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """Dapatkan daftar film populer"""
        pass

@movies_ns.route('/newest')
class NewestMovies(Resource):
    @swagger_api.doc('get_newest_movies')
    @swagger_api.marshal_list_with(movie_model)
    @swagger_api.param('page', 'Nomor halaman', type='integer', default=1)
    @swagger_api.param('genre', 'Filter genre', type='string')
    @swagger_api.param('year', 'Filter tahun', type='string')
    @swagger_api.param('show_all', 'Tampilkan semua film', type='boolean', default=False)
    @swagger_api.response(200, 'Success', pagination_model)
    @swagger_api.response(400, 'Bad Request', error_model)
    @swagger_api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """Dapatkan daftar film terbaru"""
        pass

@movies_ns.route('/<int:movie_id>')
class MovieDetail(Resource):
    @swagger_api.doc('get_movie_detail')
    @swagger_api.marshal_with(movie_model)
    @swagger_api.param('movie_id', 'ID film', required=True, type='integer')
    @swagger_api.response(200, 'Success', movie_model)
    @swagger_api.response(404, 'Movie Not Found', error_model)
    @swagger_api.response(500, 'Internal Server Error', error_model)
    def get(self, movie_id):
        """Dapatkan detail film berdasarkan ID"""
        pass

# Search endpoints documentation
@search_ns.route('')
class MovieSearch(Resource):
    @swagger_api.doc('search_movies')
    @swagger_api.marshal_list_with(movie_model)
    @swagger_api.param('q', 'Query pencarian', required=True, type='string')
    @swagger_api.param('page', 'Nomor halaman', type='integer', default=1)
    @swagger_api.param('show_all', 'Tampilkan semua hasil', type='boolean', default=False)
    @swagger_api.response(200, 'Success', pagination_model)
    @swagger_api.response(400, 'Bad Request', error_model)
    @swagger_api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """Cari film berdasarkan query"""
        pass

# Genre endpoints documentation
@genres_ns.route('')
class GenreList(Resource):
    @swagger_api.doc('get_genres')
    @swagger_api.marshal_list_with(genre_model)
    @swagger_api.response(200, 'Success', genre_model)
    @swagger_api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """Dapatkan daftar genre yang tersedia"""
        pass

# Recommendation endpoints documentation
@recommendations_ns.route('/<int:movie_id>')
class MovieRecommendations(Resource):
    @swagger_api.doc('get_movie_recommendations')
    @swagger_api.marshal_list_with(recommendation_model)
    @swagger_api.param('movie_id', 'ID film', required=True, type='integer')
    @swagger_api.param('top_n', 'Jumlah rekomendasi', type='integer', default=10)
    @swagger_api.response(200, 'Success', recommendation_model)
    @swagger_api.response(404, 'Movie Not Found', error_model)
    @swagger_api.response(500, 'Internal Server Error', error_model)
    def get(self, movie_id):
        """Dapatkan rekomendasi film serupa"""
        pass

# API Info endpoint
@swagger_api.route('/info')
class APIInfo(Resource):
    @swagger_api.doc('get_api_info')
    @swagger_api.response(200, 'Success')
    def get(self):
        """Dapatkan informasi API"""
        return {
            'name': 'FilmKu API',
            'version': '1.0.0',
            'description': 'API untuk aplikasi rekomendasi film Indonesia',
            'endpoints': {
                'movies': '/api/movies',
                'search': '/api/search',
                'genres': '/api/genres',
                'recommendations': '/api/movie/{id}/recommendations'
            },
            'documentation': '/docs/'
        }

# Health check endpoint
# Health endpoint disediakan oleh app/__init__.py (/health).
# Swagger tidak mendaftarkan /health agar tidak bertabrakan dengan test.


def init_swagger(app):
    """Initialize Swagger documentation"""
    swagger_api.init_app(app)
    return swagger_api
