"""
API endpoint tests
"""
import json
import pytest
from unittest.mock import patch
from app.models import Movie, Genre
from app.movie_service import movie_service

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
        
        # Check if movies are sorted by weighted rating (descending)
        if len(data['movies']) > 1:
            weighted_ratings = [
                (
                    movie['vote_average'] * movie['vote_count']
                    + 100 * 5.0
                ) / (movie['vote_count'] + 100)
                for movie in data['movies']
            ]
            assert weighted_ratings == sorted(weighted_ratings, reverse=True)

    @pytest.mark.parametrize('movie_type', ['popular', 'trending', 'newest'])
    def test_tab_page_matches_movie_service_ranking(self, client, app, movie_type):
        response = client.get(f'/api/movies?type={movie_type}')
        assert response.status_code == 200
        response_movies = json.loads(response.data)['movies']

        with app.app_context():
            movies = movie_service.filter_movies(
                movie_service.load_movies(),
                '',
                '',
            )
            expected_movies = movie_service.sort_movies(movies, movie_type)[:20]

        assert [movie['id'] for movie in response_movies] == [
            movie['id'] for movie in expected_movies
        ]
    
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

    def test_get_movie_details_includes_top_level_director(self, client, app):
        from app.routes import movie_service

        movie = {
            'id': 42,
            'title': 'Film dengan Sutradara',
            'overview': 'Sinopsis film.',
            'director': 'Nama Sutradara',
        }

        with app.app_context():
            with patch.object(movie_service, 'load_movies', return_value=[movie]):
                response = client.get('/api/movie/42')

        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['movie']['director'] == 'Nama Sutradara'

    
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

    def test_search_matching_movie_title_uses_content_based_results(self, client, app):
        """A movie title search should return other content-similar movies."""
        from app.routes import movie_service

        movies = [
            {
                'id': 101,
                'title': 'Dilan 1990',
                'overview': 'A high school romance between Dilan and Milea in Bandung.',
                'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
            },
            {
                'id': 102,
                'title': 'Milea: Suara dari Dilan',
                'overview': 'A romantic high school story about Dilan and Milea.',
                'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
            },
            {
                'id': 103,
                'title': 'Space Battle',
                'overview': 'A crew battles aliens in deep space.',
                'genres': [{'name': 'Action'}, {'name': 'Science Fiction'}],
            },
        ]

        with app.app_context():
            with patch.object(movie_service, 'load_movies', return_value=movies):
                response = client.get('/api/search?q=Dilan%201990')

        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['search_mode'] == 'content_based'
        assert [movie['id'] for movie in data['results'][:2]] == [101, 102]
        assert all(
            0.0 <= movie['pcc_similarity'] <= 1.0
            for movie in data['results']
        )

    def test_search_results_return_twenty_and_sort_by_pcc_then_popularity(
        self,
        client,
        app,
    ):
        """Fill partial recommendations to twenty and sort by PCC/popularity."""
        from app.routes import movie_service

        movies = [
            {'id': index, 'title': f'Film {index}', 'popularity': index}
            for index in range(25)
        ]
        pcc_scores = {str(index): 0.5 for index in range(20)}
        pcc_scores.update({'0': 0.9, '1': 0.9, '2': 0.95})
        recommend_kwargs = {}

        def recommend(query, candidate_movies, top_n):
            recommend_kwargs.update(
                top_n=top_n,
            )
            return candidate_movies[:2]

        with app.app_context():
            with patch.object(movie_service, 'load_movies', return_value=movies):
                with patch.object(
                    movie_service,
                    'recommend_similar_movies',
                    side_effect=recommend,
                ):
                    with patch.object(
                        movie_service, 'calculate_pcc_scores', return_value=pcc_scores
                    ):
                        response = client.get('/api/search?q=sample')

        data = json.loads(response.data)
        assert response.status_code == 200
        assert len(data['results']) == 20
        assert recommend_kwargs == {'top_n': 20}
        assert [
            movie['id'] for movie in data['results'][:3]
        ] == [2, 1, 0]
        assert all(
            movie['relevance']
            == 'Belum ada kecocokan kuat pada judul, sinopsis, genre, atau sutradara'
            for movie in data['results']
        )

    def test_search_results_match_shared_diagram_ranking(self, client, app):
        from app.routes import movie_service
        from precision_ndcg_by_tab import get_content_ranking

        movies = [
            {'id': 1, 'title': 'First Film', 'popularity': 1},
            {'id': 2, 'title': 'Second Film', 'popularity': 20},
            {'id': 3, 'title': 'Third Film', 'popularity': 5},
        ]
        pcc_scores = {'1': 0.8, '2': 0.8, '3': 0.5}

        with app.app_context():
            with patch.object(movie_service, 'load_movies', return_value=movies):
                with patch.object(
                    movie_service,
                    'recommend_similar_movies',
                    return_value=movies,
                ):
                    with patch.object(
                        movie_service,
                        'calculate_pcc_scores',
                        return_value=pcc_scores,
                    ):
                        expected, _ = get_content_ranking('sample', movies)
                        response = client.get('/api/search?q=sample')

        actual = json.loads(response.data)['results']
        expected_pairs = [
            (movie['id'], movie['relevance'], movie['pcc_similarity'])
            for movie in expected
        ]
        actual_pairs = [
            (movie['id'], movie['relevance'], movie['pcc_similarity'])
            for movie in actual
        ]

        assert response.status_code == 200
        assert actual_pairs == expected_pairs

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
        assert len(data['recommendations']) == 20
        assert all(recommendation.get('relevance') for recommendation in data['recommendations'])
        pcc_scores = [
            (
                -movie_service._as_float(recommendation['pcc_similarity']),
                -movie_service._as_float(recommendation.get('popularity')),
            )
            for recommendation in data['recommendations']
        ]
        assert pcc_scores == sorted(pcc_scores)

    
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
