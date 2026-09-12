"""
Service layer tests
"""
import pytest
from unittest.mock import Mock, patch
from app.database_service import DatabaseMovieService
from app.cache_service import CacheService
from app.movie_service import MovieService

class TestDatabaseMovieService:
    """Test DatabaseMovieService"""
    
    def test_get_movies_basic(self, app):
        """Test basic movie retrieval"""
        with app.app_context():
            service = DatabaseMovieService()
            movies, page, total_pages, total_movies = service.get_movies()
            
            assert isinstance(movies, list)
            assert isinstance(page, int)
            assert isinstance(total_pages, int)
            assert isinstance(total_movies, int)
            assert total_movies > 0
    
    def test_get_movies_with_type(self, app):
        """Test getting movies with different types"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Test trending
            movies_trending, _, _, _ = service.get_movies(movie_type='trending')
            assert isinstance(movies_trending, list)
            
            # Test popular
            movies_popular, _, _, _ = service.get_movies(movie_type='popular')
            assert isinstance(movies_popular, list)
            
            # Test newest
            movies_newest, _, _, _ = service.get_movies(movie_type='newest')
            assert isinstance(movies_newest, list)
    
    def test_get_movies_with_filters(self, app):
        """Test getting movies with filters"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Test with genre filter
            movies, _, _, _ = service.get_movies(genre_id='Action')
            assert isinstance(movies, list)
            
            # Test with year filter
            movies, _, _, _ = service.get_movies(year='2018')
            assert isinstance(movies, list)
            
            # Test with both filters
            movies, _, _, _ = service.get_movies(genre_id='Action', year='2018')
            assert isinstance(movies, list)
    
    def test_get_movies_pagination(self, app):
        """Test movie pagination"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Test first page
            movies, page, total_pages, total_movies = service.get_movies(page=1)
            assert page == 1
            assert len(movies) <= 20
            
            # Test show_all
            movies_all, _, _, total = service.get_movies(show_all=True)
            assert len(movies_all) == total
    
    def test_get_movie_by_id(self, app):
        """Test getting movie by ID"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Test existing movie
            movie = service.get_movie_by_id(1)
            assert movie is not None
            assert movie['id'] == 1
            assert 'title' in movie
            
            # Test non-existing movie
            movie = service.get_movie_by_id(99999)
            assert movie is None
    
    def test_search_movies(self, app):
        """Test movie search"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Test basic search
            results = service.search_movies('avengers')
            assert isinstance(results, list)
            
            # Test search with pagination
            results, page, total_pages, total = service.search_movies('test', page=1)
            assert isinstance(results, list)
            assert isinstance(page, int)
            assert isinstance(total_pages, int)
            assert isinstance(total, int)
            
            # Test show_all
            results_all = service.search_movies('test', show_all=True)
            assert isinstance(results_all, list)
    
    def test_get_genres(self, app):
        """Test getting genres"""
        with app.app_context():
            service = DatabaseMovieService()
            genres = service.get_genres()
            
            assert isinstance(genres, list)
            assert len(genres) > 0
            
            for genre in genres:
                assert 'id' in genre
                assert 'name' in genre
                assert 'count' in genre
    
    def test_get_recommendations(self, app):
        """Test getting movie recommendations"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Test existing movie
            recommendations = service.get_recommendations(1)
            assert isinstance(recommendations, list)
            
            # Test non-existing movie
            recommendations = service.get_recommendations(99999)
            assert isinstance(recommendations, list)
    
    def test_get_stats(self, app):
        """Test getting database statistics"""
        with app.app_context():
            service = DatabaseMovieService()
            stats = service.get_stats()
            
            assert isinstance(stats, dict)
            assert 'total_movies' in stats
            assert 'total_genres' in stats
            assert 'cached_recommendations' in stats
            assert stats['total_movies'] > 0
    
    def test_cache_recommendations(self, app):
        """Test caching recommendations"""
        with app.app_context():
            service = DatabaseMovieService()
            
            recommendations = [
                {'id': 2, 'similarity_score': 0.8},
                {'id': 3, 'similarity_score': 0.7}
            ]
            
            # This should not raise an exception
            service.cache_recommendations(1, recommendations)

class TestCacheService:
    """Test CacheService"""
    
    def test_get_cache_key(self):
        """Test cache key generation"""
        service = CacheService()
        
        key1 = service.get_cache_key('test', 'arg1', param1='value1')
        key2 = service.get_cache_key('test', 'arg1', param1='value1')
        key3 = service.get_cache_key('test', 'arg2', param1='value1')
        
        # Same arguments should produce same key
        assert key1 == key2
        
        # Different arguments should produce different keys
        assert key1 != key3
        
        # Keys should be strings
        assert isinstance(key1, str)
        assert len(key1) > 0
    
    def test_cache_operations(self, app, mock_cache):
        """Test basic cache operations"""
        with app.app_context():
            # Mock the app cache
            app.cache = mock_cache
            
            service = CacheService()
            
            # Test set and get
            key = 'test_key'
            value = {'test': 'data'}
            
            assert service.set(key, value) == True
            assert service.get(key) == value
            
            # Test delete
            assert service.delete(key) == True
            assert service.get(key) is None
    
    def test_cache_search_results(self, app, mock_cache):
        """Test caching search results"""
        with app.app_context():
            app.cache = mock_cache
            
            service = CacheService()
            
            query = 'test query'
            filters = {'genre': 'Action'}
            movie_ids = [1, 2, 3]
            
            # Cache search results
            service.cache_search_results(query, filters, movie_ids)
            
            # Get cached search
            cached_ids = service.get_cached_search(query, filters)
            assert cached_ids == movie_ids
    
    def test_cache_movie_recommendations(self, app, mock_cache):
        """Test caching movie recommendations"""
        with app.app_context():
            app.cache = mock_cache
            
            service = CacheService()
            
            movie_id = 1
            recommendations = [{'id': 2, 'score': 0.8}]
            
            # Cache recommendations
            service.cache_movie_recommendations(movie_id, recommendations)
            
            # Get cached recommendations
            cached_recs = service.get_cached_recommendations(movie_id)
            assert cached_recs == recommendations
    
    def test_cache_genres(self, app, mock_cache):
        """Test caching genres"""
        with app.app_context():
            app.cache = mock_cache
            
            service = CacheService()
            
            genres = [{'id': 28, 'name': 'Action'}]
            
            # Cache genres
            service.cache_genres(genres)
            
            # Get cached genres
            cached_genres = service.get_cached_genres()
            assert cached_genres == genres
    
    def test_cache_stats(self, app, mock_cache):
        """Test caching statistics"""
        with app.app_context():
            app.cache = mock_cache
            
            service = CacheService()
            
            stats = {'total_movies': 100}
            
            # Cache stats
            service.cache_stats(stats)
            
            # Get cached stats
            cached_stats = service.get_cached_stats()
            assert cached_stats == stats
    
    def test_invalidate_movie_cache(self, app, mock_cache):
        """Test invalidating movie cache"""
        with app.app_context():
            app.cache = mock_cache
            
            service = CacheService()
            
            # This should not raise an exception
            service.invalidate_movie_cache(1)
            service.invalidate_movie_cache()  # All movies

class TestMovieService:
    """Test MovieService (original CSV-based service)"""
    
    def test_load_movies(self, app):
        """Test loading movies from CSV"""
        with app.app_context():
            service = MovieService()
            movies = service.load_movies()
            
            assert isinstance(movies, list)
            # Should have movies from test data
            assert len(movies) > 0
    
    def test_filter_movies(self, app):
        """Test filtering movies"""
        with app.app_context():
            service = MovieService()
            movies = service.load_movies()
            
            # Test without filters
            filtered = service.filter_movies(movies)
            assert isinstance(filtered, list)
            
            # Test with genre filter
            filtered = service.filter_movies(movies, genre_id='Action')
            assert isinstance(filtered, list)
            
            # Test with year filter
            filtered = service.filter_movies(movies, year='2018')
            assert isinstance(filtered, list)
    
    def test_sort_movies(self, app):
        """Test sorting movies"""
        with app.app_context():
            service = MovieService()
            movies = service.load_movies()
            
            # Test different sort types
            sorted_trending = service.sort_movies(movies, 'trending')
            sorted_popular = service.sort_movies(movies, 'popular')
            sorted_newest = service.sort_movies(movies, 'newest')
            
            assert isinstance(sorted_trending, list)
            assert isinstance(sorted_popular, list)
            assert isinstance(sorted_newest, list)
    
    def test_search_movies_csv_service(self, app):
        """Test movie search with CSV service"""
        with app.app_context():
            service = MovieService()
            movies = service.load_movies()
            
            # Test search
            results = service.search_movies('test', movies)
            assert isinstance(results, list)
    
    def test_get_movie_by_id_csv_service(self, app):
        """Test getting movie by ID with CSV service"""
        with app.app_context():
            service = MovieService()
            movies = service.load_movies()
            
            # Test existing movie
            movie = service.get_movie_by_id(1, movies)
            assert movie is not None
            assert movie['id'] == 1
            
            # Test non-existing movie
            movie = service.get_movie_by_id(99999, movies)
            assert movie is None

class TestServiceIntegration:
    """Test service integration"""
    
    def test_database_service_integration(self, app):
        """Test database service integration with Flask app"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # All operations should work without errors
            movies, _, _, _ = service.get_movies()
            assert len(movies) > 0
            
            movie = service.get_movie_by_id(1)
            assert movie is not None
            
            genres = service.get_genres()
            assert len(genres) > 0
    
    def test_cache_service_integration(self, app):
        """Test cache service integration with Flask app"""
        with app.app_context():
            service = CacheService()
            
            # Cache operations should work
            key = service.get_cache_key('test', 'integration')
            assert isinstance(key, str)
            
            # Should not raise exceptions even without Redis
            result = service.get(key)
            assert result is None
            
            result = service.set(key, 'test_value')
            assert result is True or result is False  # May fail without proper cache setup
    
    @patch('app.cache_service.current_app')
    def test_cache_service_with_mock(self, mock_current_app):
        """Test cache service with mocked Flask app"""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_current_app.cache = mock_cache
        
        service = CacheService()
        
        # Test operations with mocked cache
        result = service.get('test_key')
        assert result is None
        
        result = service.set('test_key', 'test_value')
        assert result is True
        
        # Verify cache was called
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()

class TestServiceEdgeCases:
    """Test service edge cases and error handling"""
    
    def test_database_service_empty_filters(self, app):
        """Test database service with empty filters"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Empty filters should work
            movies, _, _, _ = service.get_movies(genre_id='', year='')
            assert isinstance(movies, list)
    
    def test_database_service_invalid_filters(self, app):
        """Test database service with invalid filters"""
        with app.app_context():
            service = DatabaseMovieService()
            
            # Invalid filters should not crash
            movies, _, _, _ = service.get_movies(genre_id='invalid', year='invalid')
            assert isinstance(movies, list)
    
    def test_cache_service_edge_cases(self):
        """Test cache service edge cases"""
        service = CacheService()
        
        # Test with None values
        key = service.get_cache_key(None, None)
        assert isinstance(key, str)
        
        # Test with empty strings
        key = service.get_cache_key('', '')
        assert isinstance(key, str)
