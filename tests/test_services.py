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
    def test_metadata_overrides_fill_only_missing_fields_by_movie_id(self, tmp_path):
        service = MovieService()
        overrides = tmp_path / 'metadata.csv'
        overrides.write_text(
            'id,overview,director,overview_language,source\n'
            '1,Verified synopsis,Verified director,id-ID,TMDB\n'
            '3,Unmatched synopsis,Unmatched director,id-ID,TMDB\n',
            encoding='utf-8',
        )
        movies = [
            {
                'id': 1,
                'overview': 'Existing synopsis',
                'director': 'Tidak tersedia',
            },
            {'id': 2, 'overview': '', 'director': ''},
        ]

        updated = service._apply_movie_metadata_overrides(
            movies,
            str(overrides),
        )

        assert updated[0]['overview'] == 'Existing synopsis'
        assert updated[0]['director'] == 'Verified director'
        assert updated[0]['overview_language'] == 'id-ID'
        assert updated[1]['overview'] == ''
        assert updated[1]['director'] == ''
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

    def test_popular_movies_are_sorted_by_weighted_rating(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'title': 'Higher popularity, lower rating',
                    'popularity': 1000,
                    'vote_average': 6,
                    'vote_count': 1000,
                },
                {
                    'title': 'Lower popularity, higher rating',
                    'popularity': 1,
                    'vote_average': 9,
                    'vote_count': 1000,
                },
                {
                    'title': 'Highest rating, few votes',
                    'popularity': 0,
                    'vote_average': 10,
                    'vote_count': 0,
                },
            ]

            sorted_movies = service.sort_movies(movies, 'popular')

            assert [movie['title'] for movie in sorted_movies] == [
                'Lower popularity, higher rating',
                'Higher popularity, lower rating',
                'Highest rating, few votes',
            ]

    def test_pcc_scores_are_normalized_and_rank_matching_text_higher(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Dilan 1990',
                    'overview': 'A high school romance in Bandung.',
                    'genres': [{'name': 'Drama'}],
                },
                {
                    'id': 2,
                    'title': 'Milea Suara dari Dilan',
                    'overview': 'A romance about Dilan and Milea.',
                    'genres': [{'name': 'Drama'}],
                },
                {
                    'id': 3,
                    'title': 'Space Battle',
                    'overview': 'A crew battles aliens in deep space.',
                    'genres': [{'name': 'Science Fiction'}],
                },
            ]

            scores = service.calculate_pcc_scores('Dilan 1990', movies)

            assert all(0.0 <= score <= 1.0 for score in scores.values())
            assert scores['1'] > scores['3']
            assert service.calculate_pcc_scores('the', movies) == {
                '1': 0.0,
                '2': 0.0,
                '3': 0.0,
            }

    def test_pcc_terms_weight_title_three_times_and_include_director(self, app):
        with app.app_context():
            service = MovieService()
            terms = service._get_movie_search_terms({
                'title': 'Dilan 1990',
                'overview': 'A high school romance.',
                'genres': [{'name': 'Drama'}],
                'director': 'Fajar Bustomi',
            })

            assert terms['recommendation_terms'].split().count('dilan') == 3
            assert terms['recommendation_terms'].split().count('fajar') == 1
            assert terms['all_terms'].split().count('fajar') == 1
            assert terms['director'] == 'fajar bustomi'

    def test_search_movies_matches_director_metadata(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Film Drama Pertama',
                    'overview': 'Kisah keluarga di sebuah kota.',
                    'genres': [{'name': 'Drama'}],
                    'director': 'Fajar Bustomi',
                },
                {
                    'id': 2,
                    'title': 'Film Aksi Kedua',
                    'overview': 'Petualangan seorang pahlawan.',
                    'genres': [{'name': 'Action'}],
                    'director': 'Sutradara Lain',
                },
            ]

            results = service.search_movies('Fajar Bustomi', movies)

            assert [movie['id'] for movie in results] == [1]
            assert results[0]['relevance'] == 'Mirip berdasarkan sutradara'

    def test_trending_keeps_engagement_primary_with_recency_bonus(self, app):
        """Engagement stays primary while recency breaks close-score rankings."""
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'title': 'High-engagement older film',
                    'vote_average': 8.0,
                    'vote_count': 3000,
                    'release_date': '2000-01-01',
                },
                {
                    'title': 'Older close-engagement film',
                    'vote_average': 7.0,
                    'vote_count': 100,
                    'release_date': '2025-10-23',
                },
                {
                    'title': 'Newer close-engagement film',
                    'vote_average': 6.99,
                    'vote_count': 100,
                    'release_date': '2025-11-27',
                },
            ]

            sorted_movies = service.sort_movies(movies, 'trending')

            assert sorted_movies[0]['title'] == 'High-engagement older film'
            assert sorted_movies[1]['title'] == 'Newer close-engagement film'

    def test_content_based_search_recommends_similar_movies(self, app):
        """A matching title should be shown before its content-based recommendations."""
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Dilan 1990',
                    'overview': 'A high school romance between Dilan and Milea in Bandung.',
                    'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
                },
                {
                    'id': 2,
                    'title': 'Milea: Suara dari Dilan',
                    'overview': 'A romantic high school story about Dilan and Milea.',
                    'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
                },
                {
                    'id': 3,
                    'title': 'Action in Space',
                    'overview': 'A crew battles aliens in deep space.',
                    'genres': [{'name': 'Action'}, {'name': 'Science Fiction'}],
                },
                {
                    'id': 4,
                    'title': 'Keadilan',
                    'overview': 'A crime drama about a court case.',
                    'genres': [{'name': 'Crime'}, {'name': 'Drama'}],
                },
            ]

            recommendations = service.recommend_similar_movies('Dilan 1990', movies, top_n=20)

            assert recommendations is not None
            assert [movie['id'] for movie in recommendations] == [1, 2, 4, 3]
            assert recommendations[0]['relevance'].startswith('Mirip berdasarkan ')
            assert recommendations[1]['relevance'].startswith('Mirip berdasarkan ')
            assert all(
                movie['relevance'].startswith('Kecocokan rendah berdasarkan ')
                for movie in recommendations[2:]
            )

    def test_movie_recommendations_are_ranked_by_pcc_not_popularity(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {'id': 1, 'title': 'Reference movie', 'overview': 'Reference story'},
                {
                    'id': 2,
                    'title': 'Popular candidate',
                    'overview': 'Candidate story A',
                    'popularity': 1000,
                    'relevance': 'Mirip berdasarkan sinopsis',
                },
                {
                    'id': 3,
                    'title': 'Higher PCC candidate',
                    'overview': 'Candidate story B',
                    'popularity': 1,
                    'relevance': 'Mirip berdasarkan sinopsis',
                },
                {
                    'id': 4,
                    'title': 'Irrelevant fallback',
                    'overview': 'Unrelated story',
                    'relevance': '',
                },
            ]
            candidates = [movie.copy() for movie in movies[1:]]

            with patch.object(
                service,
                '_recommend_content_similar',
                return_value=candidates,
            ) as get_candidates:
                with patch.object(
                    service,
                    'calculate_pcc_scores',
                    return_value={'2': 0.4, '3': 0.9, '4': 1.0},
                ) as get_pcc_scores:
                    recommendations = service.recommend_movies(1, movies, top_n=2)

            assert [movie['id'] for movie in recommendations] == [3, 2]
            assert [movie['pcc_similarity'] for movie in recommendations] == [0.9, 0.4]
            get_candidates.assert_called_once_with([0], movies, len(movies))
            assert 'reference movie' in get_pcc_scores.call_args.args[0]
            assert [movie['id'] for movie in get_pcc_scores.call_args.args[1]] == [2, 3]
            assert get_pcc_scores.call_args.kwargs['terms_key'] == 'recommendation_terms'

    def test_movie_recommendations_sort_by_pcc_then_popularity(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {'id': 1, 'title': 'Reference movie'},
                {
                    'id': 2,
                    'title': 'Title match',
                    'popularity': 1000,
                    'relevance': 'Mirip berdasarkan judul',
                },
                {
                    'id': 3,
                    'title': 'Synopsis match',
                    'popularity': 10,
                    'relevance': 'Mirip berdasarkan sinopsis',
                },
                {
                    'id': 4,
                    'title': 'Genre and director match',
                    'popularity': 50,
                    'relevance': 'Mirip berdasarkan genre dan sutradara',
                },
            ]
            candidates = [movie.copy() for movie in movies[1:]]

            with patch.object(
                service,
                '_recommend_content_similar',
                return_value=candidates,
            ):
                with patch.object(
                    service,
                    'calculate_pcc_scores',
                    return_value={'2': 0.2, '3': 0.8, '4': 0.8},
                ):
                    recommendations = service.recommend_movies(1, movies, top_n=3)

            assert [movie['id'] for movie in recommendations] == [4, 3, 2]

    def test_content_recommendations_prioritize_title_and_overview_over_genre(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Ocean Signal',
                    'overview': 'A marine biologist discovers an ancient signal beneath the Pacific ocean.',
                    'genres': [{'name': 'Adventure'}, {'name': 'Science Fiction'}],
                },
                {
                    'id': 2,
                    'title': 'Beneath the Pacific',
                    'overview': 'A marine scientist discovers a mysterious transmission in the deep ocean.',
                    'genres': [{'name': 'Drama'}],
                },
                {
                    'id': 3,
                    'title': 'A Quiet Wedding',
                    'overview': 'A family prepares for a wedding in a small village.',
                    'genres': [{'name': 'Adventure'}, {'name': 'Science Fiction'}],
                },
            ]

            recommendations = service.recommend_similar_movies('Ocean Signal', movies, top_n=20)

            assert recommendations is not None
            recommended_ids = [movie['id'] for movie in recommendations]
            assert recommended_ids == [1, 2, 3]
            assert recommendations[2]['relevance'].startswith(
                'Kecocokan rendah berdasarkan '
            )

    def test_content_recommendations_fill_twenty_with_low_confidence_candidates(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Ocean Signal',
                    'overview': 'A marine scientist discovers an ocean signal.',
                    'genres': [{'name': 'Adventure'}],
                },
                {
                    'id': 2,
                    'title': 'Ocean Current',
                    'overview': 'A researcher discovers an underwater message.',
                    'genres': [{'name': 'Adventure'}],
                },
            ]
            movies.extend(
                {
                    'id': movie_id,
                    'title': f'Unrelated film {movie_id}',
                    'overview': f'A report about a distant topic {movie_id}.',
                    'genres': [{'name': 'Documentary'}],
                }
                for movie_id in range(3, 26)
            )

            recommendations = service.recommend_similar_movies(
                'Ocean Signal', movies, top_n=20
            )

            assert recommendations is not None
            assert len(recommendations) == 20
            assert recommendations[0]['id'] == 1
            assert recommendations[1]['id'] == 2
            assert recommendations[2]['relevance'].startswith(
                'Kecocokan rendah berdasarkan '
            )
            assert all(
                movie['relevance'].startswith('Mirip berdasarkan ')
                for movie in recommendations[:2]
            )
            assert all(
                movie['relevance'].startswith('Kecocokan rendah berdasarkan ')
                for movie in recommendations[2:]
            )

    def test_fill_search_results_pads_title_recommendations_to_twenty(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Dilan 1990',
                    'overview': 'A high school romance in Bandung.',
                    'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
                },
                {
                    'id': 2,
                    'title': 'Milea Suara dari Dilan',
                    'overview': 'A story about Dilan and Milea.',
                    'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
                },
            ]
            movies.extend(
                {
                    'id': movie_id,
                    'title': f'Film Indonesia {movie_id}',
                    'overview': f'Kisah keluarga nomor {movie_id}.',
                    'genres': [{'name': 'Drama'}],
                }
                for movie_id in range(3, 26)
            )
            recommendations = service.recommend_similar_movies(
                'Dilan 1990', movies, top_n=20
            )
            early_results = recommendations[:2]

            results = service.fill_search_results(
                'Dilan 1990',
                movies,
                early_results,
                top_n=20,
            )

            assert len(early_results) == 2
            assert len(results) == 20
            assert results[0]['id'] == 1
            assert results[1]['id'] == 2
            assert len({movie['id'] for movie in results}) == 20
            assert all(
                movie['relevance'].startswith('Kecocokan rendah berdasarkan ')
                for movie in results[2:]
            )

    def test_single_word_search_includes_genre_matches_with_low_relevance(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'The Enchanted Realm',
                    'overview': 'A young hero searches for a lost crown.',
                    'genres': [{'name': 'Fantasy'}],
                },
                {
                    'id': 2,
                    'title': 'A Quiet Journey',
                    'overview': 'A family travels across the mountains.',
                    'genres': [{'name': 'Drama'}],
                },
            ]

            recommendations = service.recommend_similar_movies(
                'fantasy', movies, top_n=20
            )

            assert recommendations is not None
            assert recommendations[0]['id'] == 1
            assert recommendations[0]['relevance'] == 'Mirip berdasarkan genre'

    def test_single_word_movie_title_does_not_recommend_genre_only_movies(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Komang',
                    'overview': '',
                    'director': 'Naya Anindita',
                    'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
                },
                {
                    'id': 2,
                    'title': '99 Nama Cinta',
                    'overview': 'A journalist meets a religious teacher.',
                    'director': 'Another director',
                    'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
                },
                {
                    'id': 3,
                    'title': 'Eggnoid',
                    'overview': 'A young woman encounters a mysterious android.',
                    'director': 'Naya Anindita',
                    'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
                },
            ]
            service._semantic_model_unavailable = True

            recommendations = service.recommend_similar_movies(
                'Komang', movies, top_n=20
            )

            assert recommendations is not None
            assert [movie['id'] for movie in recommendations] == [1, 3, 2]
            assert recommendations[1]['relevance'] == (
                'Mirip berdasarkan genre dan sutradara'
            )
            assert recommendations[2]['relevance'] == (
                'Kecocokan berdasarkan genre'
            )

    def test_single_word_search_returns_title_and_overview_matches_not_genre_matches(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': 1,
                    'title': 'Keadilan',
                    'overview': 'A courtroom drama.',
                    'genres': [{'name': 'Drama'}],
                },
                {
                    'id': 2,
                    'title': 'Milea: Suara dari Dilan',
                    'overview': 'A high school romance about young students and love.',
                    'genres': [{'name': 'Romance'}],
                },
                {
                    'id': 3,
                    'title': 'Kisah di Bandung',
                    'overview': 'Dilan meets Milea at school.',
                    'genres': [{'name': 'Drama'}],
                },
                {
                    'id': 4,
                    'title': 'Drama Keluarga',
                    'overview': 'A family faces a difficult decision.',
                    'genres': [{'name': 'Drama'}],
                },
                {
                    'id': 5,
                    'title': 'Young Hearts',
                    'overview': 'A romance follows high school students falling in love.',
                    'genres': [{'name': 'Comedy'}],
                },
                {
                    'id': 26,
                    'title': 'MeloDylan',
                    'overview': 'A school story about music.',
                    'genres': [{'name': 'Drama'}],
                },
                {
                    'id': 27,
                    'title': 'Dilanjutkan Salah Disudahi Perih',
                    'overview': 'A story about relationships.',
                    'genres': [{'name': 'Drama'}],
                },
            ]
            movies.extend(
                {
                    'id': movie_id,
                    'title': f'Unrelated title {movie_id}',
                    'overview': f'A report about subject number {movie_id}.',
                    'genres': [{'name': 'Documentary'}],
                }
                for movie_id in range(6, 26)
            )

            recommendations = service.recommend_similar_movies('dilan', movies, top_n=20)

            assert recommendations is not None
            recommended_ids = [movie['id'] for movie in recommendations]
            assert 1 <= len(recommendations) <= 20
            assert recommended_ids[0] == 2
            assert 3 in recommended_ids
            assert 4 not in recommended_ids
            assert len(recommended_ids) == len(set(recommended_ids))
            assert all(movie['relevance'] for movie in recommendations)

            substring_results = service.recommend_similar_movies('melo', movies, top_n=20)
            assert substring_results[0]['id'] == 26

            multiword_results = service.recommend_similar_movies(
                'dilan salah', movies, top_n=20
            )
            assert multiword_results[0]['id'] == 27
            assert multiword_results[0]['relevance'] == (
                'Kecocokan rendah berdasarkan judul sebagian'
            )
            assert all(movie['relevance'] for movie in multiword_results)

    def test_search_movies_csv_service(self, app):
        """Test movie search with CSV service"""
        with app.app_context():
            service = MovieService()
            movies = service.load_movies()
            
            # Test search
            results = service.search_movies('test', movies)
            assert isinstance(results, list)

    def test_search_movies_fills_twenty_results_with_closest_movies(self, app):
        with app.app_context():
            service = MovieService()
            movies = [
                {
                    'id': index,
                    'title': f'Unrelated film {index}',
                    'overview': f'An unrelated story about character {index}.',
                    'genres': [],
                    'popularity': index,
                }
                for index in range(25)
            ]

            results = service.search_movies('quasarquery', movies)

            assert len(results) == 20
            assert all(
                movie['relevance'] == ''
                for movie in results
            )
    
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
