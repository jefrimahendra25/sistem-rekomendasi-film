"""
API Documentation Routes
"""
from flask import Blueprint, render_template_string, jsonify
from .swagger import swagger_api

# Create blueprint for documentation
docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/')
def api_documentation():
    """Render API documentation page"""
    html_template = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FilmKu API Documentation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .endpoint-card {
            margin-bottom: 2rem;
            border: 1px solid #dee2e6;
            border-radius: 0.375rem;
        }
        .endpoint-header {
            background-color: #f8f9fa;
            padding: 1rem;
            border-bottom: 1px solid #dee2e6;
        }
        .method-badge {
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-weight: bold;
        }
        .method-get { background-color: #28a745; color: white; }
        .method-post { background-color: #007bff; color: white; }
        .method-put { background-color: #ffc107; color: black; }
        .method-delete { background-color: #dc3545; color: white; }
        .code-block {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 1rem;
            font-family: 'Courier New', monospace;
        }
        .param-table th {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-film me-2"></i>FilmKu API
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/docs/">Documentation</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/docs/swagger">Swagger UI</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/health">Health Check</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1><i class="fas fa-book me-2"></i>FilmKu API Documentation</h1>
                <p class="lead">API untuk aplikasi rekomendasi film Indonesia dengan fitur pencarian, filtering, dan rekomendasi berbasis AI.</p>
                
                <div class="alert alert-info">
                    <h5><i class="fas fa-info-circle me-2"></i>Quick Start</h5>
                    <p>Base URL: <code>{{ request.host_url }}api</code></p>
                    <p>Authentication: Tidak diperlukan untuk endpoint publik</p>
                    <p>Format: JSON</p>
                </div>

                <h2 class="mt-5 mb-3"><i class="fas fa-film me-2"></i>Movie Endpoints</h2>
                
                <!-- Get Trending Movies -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Get Trending Movies
                        </h5>
                        <code class="text-muted">/api/movies/trending</code>
                    </div>
                    <div class="card-body">
                        <p>Mendapatkan daftar film yang sedang trending.</p>
                        
                        <h6>Query Parameters:</h6>
                        <table class="table table-sm param-table">
                            <thead>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Type</th>
                                    <th>Required</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code>page</code></td>
                                    <td>integer</td>
                                    <td>No</td>
                                    <td>Nomor halaman (default: 1)</td>
                                </tr>
                                <tr>
                                    <td><code>genre</code></td>
                                    <td>string</td>
                                    <td>No</td>
                                    <td>Filter berdasarkan genre ID atau nama</td>
                                </tr>
                                <tr>
                                    <td><code>year</code></td>
                                    <td>string</td>
                                    <td>No</td>
                                    <td>Filter berdasarkan tahun rilis</td>
                                </tr>
                                <tr>
                                    <td><code>show_all</code></td>
                                    <td>boolean</td>
                                    <td>No</td>
                                    <td>Tampilkan semua film tanpa pagination</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h6>Example Request:</h6>
                        <div class="code-block">GET /api/movies/trending?page=1&genre=Action</div>
                        
                        <h6>Response:</h6>
                        <div class="code-block">
{
    "status": "success",
    "movies": [...],
    "page": 1,
    "total_pages": 10,
    "total_movies": 200,
    "items_per_page": 20
}
                        </div>
                    </div>
                </div>

                <!-- Get Popular Movies -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Get Popular Movies
                        </h5>
                        <code class="text-muted">/api/movies/popular</code>
                    </div>
                    <div class="card-body">
                        <p>Mendapatkan daftar film populer berdasarkan rating dan jumlah vote.</p>
                        <p><strong>Parameters:</strong> Sama seperti endpoint trending</p>
                    </div>
                </div>

                <!-- Get Newest Movies -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Get Newest Movies
                        </h5>
                        <code class="text-muted">/api/movies/newest</code>
                    </div>
                    <div class="card-body">
                        <p>Mendapatkan daftar film terbaru berdasarkan tanggal rilis.</p>
                        <p><strong>Parameters:</strong> Sama seperti endpoint trending</p>
                    </div>
                </div>

                <!-- Get Movie Details -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Get Movie Details
                        </h5>
                        <code class="text-muted">/api/movie/{movie_id}</code>
                    </div>
                    <div class="card-body">
                        <p>Mendapatkan detail lengkap film berdasarkan ID.</p>
                        
                        <h6>Path Parameters:</h6>
                        <table class="table table-sm param-table">
                            <thead>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Type</th>
                                    <th>Required</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code>movie_id</code></td>
                                    <td>integer</td>
                                    <td>Yes</td>
                                    <td>ID unik film</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h6>Example Request:</h6>
                        <div class="code-block">GET /api/movie/1</div>
                    </div>
                </div>

                <h2 class="mt-5 mb-3"><i class="fas fa-search me-2"></i>Search Endpoints</h2>
                
                <!-- Search Movies -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Search Movies
                        </h5>
                        <code class="text-muted">/api/search</code>
                    </div>
                    <div class="card-body">
                        <p>Mencari film berdasarkan judul, sutradara, atau kata kunci.</p>
                        
                        <h6>Query Parameters:</h6>
                        <table class="table table-sm param-table">
                            <thead>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Type</th>
                                    <th>Required</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code>q</code></td>
                                    <td>string</td>
                                    <td>Yes</td>
                                    <td>Query pencarian</td>
                                </tr>
                                <tr>
                                    <td><code>page</code></td>
                                    <td>integer</td>
                                    <td>No</td>
                                    <td>Nomor halaman (default: 1)</td>
                                </tr>
                                <tr>
                                    <td><code>show_all</code></td>
                                    <td>boolean</td>
                                    <td>No</td>
                                    <td>Tampilkan semua hasil</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h6>Example Request:</h6>
                        <div class="code-block">GET /api/search?q=avengers&page=1</div>
                        
                        <h6>Response:</h6>
                        <div class="code-block">
{
    "status": "success",
    "query": "avengers",
    "results": [...],
    "page": 1,
    "total_pages": 2,
    "total_results": 25,
    "items_per_page": 20
}
                        </div>
                    </div>
                </div>

                <h2 class="mt-5 mb-3"><i class="fas fa-tags me-2"></i>Genre Endpoints</h2>
                
                <!-- Get Genres -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Get Genres
                        </h5>
                        <code class="text-muted">/api/genres</code>
                    </div>
                    <div class="card-body">
                        <p>Mendapatkan daftar genre yang tersedia beserta jumlah film dalam setiap genre.</p>
                        
                        <h6>Response:</h6>
                        <div class="code-block">
{
    "status": "success",
    "genres": [
        {
            "id": 28,
            "name": "Action",
            "count": 150
        },
        ...
    ],
    "total": 20
}
                        </div>
                    </div>
                </div>

                <h2 class="mt-5 mb-3"><i class="fas fa-magic me-2"></i>Recommendation Endpoints</h2>
                
                <!-- Get Recommendations -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Get Movie Recommendations
                        </h5>
                        <code class="text-muted">/api/movie/{movie_id}/recommendations</code>
                    </div>
                    <div class="card-body">
                        <p>Mendapatkan rekomendasi film serupa berdasarkan algoritma machine learning.</p>
                        
                        <h6>Path Parameters:</h6>
                        <table class="table table-sm param-table">
                            <thead>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Type</th>
                                    <th>Required</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code>movie_id</code></td>
                                    <td>integer</td>
                                    <td>Yes</td>
                                    <td>ID film untuk rekomendasi</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h6>Query Parameters:</h6>
                        <table class="table table-sm param-table">
                            <thead>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Type</th>
                                    <th>Required</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code>top_n</code></td>
                                    <td>integer</td>
                                    <td>No</td>
                                    <td>Jumlah rekomendasi (default: 10, max: 20)</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h6>Example Request:</h6>
                        <div class="code-block">GET /api/movie/1/recommendations?top_n=5</div>
                        
                        <h6>Response:</h6>
                        <div class="code-block">
{
    "status": "success",
    "movie": {...},
    "recommendations": [
        {
            "id": 2,
            "title": "Similar Movie",
            "similarity_score": 0.85,
            "recommendation_type": "hybrid"
        },
        ...
    ],
    "total_recommendations": 5
}
                        </div>
                    </div>
                </div>

                <h2 class="mt-5 mb-3"><i class="fas fa-heartbeat me-2"></i>Utility Endpoints</h2>
                
                <!-- Health Check -->
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <h5>
                            <span class="method-badge method-get me-2">GET</span>
                            Health Check
                        </h5>
                        <code class="text-muted">/health</code>
                    </div>
                    <div class="card-body">
                        <p>Memeriksa status kesehatan API dan database.</p>
                        
                        <h6>Response:</h6>
                        <div class="code-block">
{
    "status": "healthy",
    "total_movies": 1000,
    "timestamp": "2023-12-01T10:00:00Z",
    "version": "1.0.0",
    "cache_status": "hit"
}
                        </div>
                    </div>
                </div>

                <h2 class="mt-5 mb-3"><i class="fas fa-exclamation-triangle me-2"></i>Error Responses</h2>
                
                <div class="endpoint-card">
                    <div class="card-body">
                        <p>Semua error responses mengikuti format konsisten:</p>
                        <div class="code-block">
{
    "status": "error",
    "message": "Error description",
    "code": 400
}
                        </div>
                        
                        <h6>Common HTTP Status Codes:</h6>
                        <ul>
                            <li><code>200</code> - Success</li>
                            <li><code>400</code> - Bad Request (parameter tidak valid)</li>
                            <li><code>404</code> - Not Found (resource tidak ditemukan)</li>
                            <li><code>429</code> - Too Many Requests (rate limit exceeded)</li>
                            <li><code>500</code> - Internal Server Error</li>
                        </ul>
                    </div>
                </div>

                <h2 class="mt-5 mb-3"><i class="fas fa-code me-2"></i>Code Examples</h2>
                
                <div class="endpoint-card">
                    <div class="card-body">
                        <h6>JavaScript (Fetch API):</h6>
                        <div class="code-block">
// Get trending movies
fetch('/api/movies/trending?page=1')
    .then(response => response.json())
    .then(data => console.log(data));

// Search movies
fetch('/api/search?q=avengers')
    .then(response => response.json())
    .then(data => console.log(data));
                        </div>
                        
                        <h6>Python (requests):</h6>
                        <div class="code-block">
import requests

# Get trending movies
response = requests.get('http://localhost:5002/api/movies/trending')
movies = response.json()

# Search movies
response = requests.get('http://localhost:5002/api/search?q=avengers')
results = response.json()
                        </div>
                        
                        <h6>cURL:</h6>
                        <div class="code-block">
# Get trending movies
curl -X GET "http://localhost:5002/api/movies/trending?page=1"

# Search movies
curl -X GET "http://localhost:5002/api/search?q=avengers"
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-light mt-5 py-4">
        <div class="container text-center">
            <p class="mb-0">© 2023 FilmKu API. Documentation generated with Flask-RESTX.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """
    return html_template

@docs_bp.route('/swagger')
def swagger_ui():
    """Redirect to Swagger UI"""
    return jsonify({
        'message': 'Swagger UI available at /docs/',
        'swagger_json': '/docs/swagger.json'
    })

@docs_bp.route('/swagger.json')
def swagger_json():
    """Return Swagger JSON specification"""
    return jsonify(swagger_api.__schema__)
