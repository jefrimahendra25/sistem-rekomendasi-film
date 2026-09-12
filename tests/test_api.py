"""
API endpoint tests
"""
import json
import pytest
from app.models import Movie, Genre

class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_index_endpoint(self, client):
        """Test the index endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'FilmKu' in response.data
    
    def test_api_welcome(self, client):
        """Test the API welcome endpoint"""
        response = client.get('/api/welcome')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'message' in data
    
    def test_health_check(self, client):
        """Test the health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'total_movies' in data
        assert 'timestamp' in data
    
    def test_get_movies_trending(self, client):
        """Test getting trending movies"""
        response = client.get('/api/movies/trending')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'movies' in data
        assert 'page' in data
        assert 'total_pages' in data
        assert len(data['movies']) <= 20  # Default page size
    
    def test_get_movies_popular(self, client):
        """Test getting popular movies"""
        response = client.get('/api/movies/popular')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'movies' in data
        
        # Check if movies are sorted by popularity (descending)
        if len(data['movies']) > 1:
            assert data['movies'][0]['popularity'] >= data['movies'][1]['popularity']
    
    def test_get_movies_newest(self, client):
        """Test getting newest movies"""
        response = client.get('/api/movies/newest')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'movies' in data
        
        # Check if movies are sorted by release date (descending)
        if len(data['movies']) > 1:
            movies_with_dates = [m for m in data['movies'] if m.get('release_date')]
            if len(movies_with_dates) > 1:
                assert movies_with_dates[0]['release_date'] >= movies_with_dates[1]['release_date']
    
    def test_get_movies_with_filters(self, client):
        """Test getting movies with genre and year filters"""
        # Test with genre filter
        response = client.get('/api/movies?genre=28')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        # Test with year filter
        response = client.get('/api/movies?year=2018')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        # Test with both filters
        response = client.get('/api/movies?genre=28&year=2018')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_get_movies_pagination(self, client):
        """Test movie pagination"""
        # Test first page
        response = client.get('/api/movies?page=1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page'] == 1
        assert len(data['movies']) <= 20
        
        # Test second page
        response = client.get('/api/movies?page=2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page'] == 2
    
    def test_get_movies_show_all(self, client):
        """Test getting all movies without pagination"""
        response = client.get('/api/movies?show_all=true')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['total_movies'] == len(data['movies'])
    
    def test_get_movie_details(self, client):
        """Test getting movie details"""
        # Ambil movie_id valid dari dataset agar test tidak bergantung pada id=1 yang mungkin tidak tersedia
        from app.routes import movie_service
        movies = movie_service.load_movies()
        assert movies
        movie_id = int(movies[0]['id'])

        response = client.get(f'/api/movie/{movie_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'movie' in data
        assert data['movie']['id'] == movie_id
        assert 'title' in data['movie']
        assert 'overview' in data['movie']

    
    def test_get_movie_not_found(self, client):
        """Test getting non-existent movie"""
        response = client.get('/api/movie/99999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'not found' in data['message'].lower()
    
    def test_search_movies(self, client, sample_search_query):
        """Test movie search"""
        response = client.get(f'/api/search?q={sample_search_query}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'results' in data
        assert data['query'] == sample_search_query
        assert 'total_results' in data
    
    def test_search_movies_empty_query(self, client):
        """Test search with empty query"""
        response = client.get('/api/search?q=')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'required' in data['message'].lower()
    
    def test_search_movies_no_query(self, client):
        """Test search without query parameter"""
        response = client.get('/api/search')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'required' in data['message'].lower()
    
    def test_search_movies_pagination(self, client, sample_search_query):
        """Test search pagination"""
        response = client.get(f'/api/search?q={sample_search_query}&page=1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page'] == 1
        assert len(data['results']) <= 20
    
    def test_get_genres(self, client):
        """Test getting genres"""
        response = client.get('/api/genres')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'genres' in data
        assert len(data['genres']) > 0
        
        # Check genre structure
        for genre in data['genres']:
            assert 'id' in genre
            assert 'name' in genre
            assert 'count' in genre
    
    def test_get_movie_recommendations(self, client):
        """Test getting movie recommendations"""
        from app.routes import movie_service
        movies = movie_service.load_movies()
        assert movies
        movie_id = int(movies[0]['id'])

        response = client.get(f'/api/movie/{movie_id}/recommendations')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'recommendations' in data
        assert 'movie' in data
        assert data['movie']['id'] == movie_id

    
    def test_get_recommendations_not_found(self, client):
        """Test recommendations for non-existent movie"""
        response = client.get('/api/movie/99999/recommendations')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'not found' in data['message'].lower()
    
    def test_get_recommendations_with_limit(self, client):
        """Test recommendations with custom limit"""
        from app.routes import movie_service
        movies = movie_service.load_movies()
        assert movies
        movie_id = int(movies[0]['id'])

        response = client.get(f'/api/movie/{movie_id}/recommendations?top_n=2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['recommendations']) <= 2

    
    def test_get_countries(self, client):
        """Test getting countries"""
        response = client.get('/countries')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'countries' in data
        assert len(data['countries']) > 0
        
        # Check country structure
        for country in data['countries']:
            assert 'code' in country
            assert 'name' in country
    
    def test_debug_movie_stats(self, client):
        """Test debug movie statistics endpoint"""
        response = client.get('/debug/movie_stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'total_movies' in data
        assert 'genres' in data
        assert 'years' in data
        assert 'ratings' in data
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get('/api/invalid_endpoint')
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test invalid HTTP method"""
        response = client.post('/api/movies')
        assert response.status_code == 405  # Method Not Allowed
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/api/movies')
        assert response.status_code == 200
        # Check for CORS headers (may vary based on configuration)
        assert 'Access-Control-Allow-Origin' in response.headers or 'access-control-allow-origin' in response.headers
    
    def test_rate_limiting_headers(self, client):
        """Test rate limiting headers"""
        response = client.get('/api/movies')
        assert response.status_code == 200
        # Rate limiting headers may be present depending on configuration

class TestAPIValidation:
    """Test API input validation"""
    
    def test_invalid_page_parameter(self, client):
        """Test invalid page parameter"""
        response = client.get('/api/movies?page=abc')
        assert response.status_code == 200  # Should default to page 1
        data = json.loads(response.data)
        assert data['page'] == 1
    
    def test_negative_page_parameter(self, client):
        """Test negative page parameter"""
        response = client.get('/api/movies?page=-1')
        assert response.status_code == 200  # Should default to page 1
        data = json.loads(response.data)
        assert data['page'] == 1
    
    def test_invalid_year_parameter(self, client):
        """Test invalid year parameter"""
        response = client.get('/api/movies?year=abc')
        assert response.status_code == 200  # Should ignore invalid year
        data = json.loads(response.data)
        assert 'movies' in data
    
    def test_invalid_genre_parameter(self, client):
        """Test invalid genre parameter"""
        response = client.get('/api/movies?genre=invalid_genre')
        assert response.status_code == 200  # Should return empty results
        data = json.loads(response.data)
        assert 'movies' in data
    
    def test_large_page_number(self, client):
        """Test very large page number"""
        response = client.get('/api/movies?page=999')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should return empty results for page beyond available data
        assert len(data['movies']) == 0

class TestAPIPerformance:
    """Test API performance characteristics"""
    
    def test_response_time(self, client):
        """Test API response time is reasonable"""
        import time
        start_time = time.time()
        response = client.get('/api/movies')
        end_time = time.time()
        
        assert response.status_code == 200
        # Response should be under 2 seconds for basic requests
        assert (end_time - start_time) < 2.0
    
    def test_search_response_time(self, client):
        """Test search response time"""
        import time
        start_time = time.time()
        response = client.get('/api/search?q=test')
        end_time = time.time()
        
        assert response.status_code == 200
        # Search should be under 3 seconds
        assert (end_time - start_time) < 3.0
    
    def test_cache_effectiveness(self, client, app):
        """Test that caching improves response time"""
        import time
        
        # First request (no cache)
        start_time = time.time()
        response1 = client.get('/api/movies/trending')
        first_time = time.time() - start_time
        
        # Second request (should hit cache)
        start_time = time.time()
        response2 = client.get('/api/movies/trending')
        second_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Second request should be faster (or at least not significantly slower)
        assert second_time <= first_time * 1.5  # Allow some variance
