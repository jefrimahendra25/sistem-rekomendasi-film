"""
Model tests
"""
import pytest
import json
from datetime import datetime, date
from app.models import db, Movie, Genre, MovieRecommendation, SearchCache, UserRating

class TestMovieModel:
    """Test Movie model"""
    
    def test_create_movie(self, app):
        """Test creating a movie"""
        with app.app_context():
            movie = Movie(
                id=100,
                tmdb_id=1000,
                title='Test Movie',
                overview='Test overview',
                release_date=date(2023, 1, 1),
                popularity=50.0,
                vote_average=8.5,
                vote_count=1000,
                poster_path='/test.jpg',
                original_language='en',
                runtime=120,
                director='Test Director'
            )
            
            db.session.add(movie)
            db.session.commit()
            
            retrieved_movie = Movie.query.filter_by(id=100).first()
            assert retrieved_movie is not None
            assert retrieved_movie.title == 'Test Movie'
            assert retrieved_movie.vote_average == 8.5
            assert retrieved_movie.release_date == date(2023, 1, 1)
    
    def test_movie_to_dict(self, app):
        """Test movie to_dict method"""
        with app.app_context():
            movie = Movie(
                id=101,
                tmdb_id=1001,
                title='Test Movie 2',
                overview='Test overview 2',
                release_date=date(2023, 2, 1),
                popularity=60.0,
                vote_average=9.0,
                vote_count=2000,
                poster_path='/test2.jpg',
                original_language='en',
                runtime=130,
                director='Test Director 2'
            )
            
            movie_dict = movie.to_dict()
            
            assert movie_dict['id'] == 101
            assert movie_dict['title'] == 'Test Movie 2'
            assert movie_dict['vote_average'] == 9.0
            assert movie_dict['release_date'] == '2023-02-01'
            assert 'created_at' in movie_dict
            assert 'updated_at' in movie_dict
    
    def test_movie_genre_methods(self, app):
        """Test movie genre getter/setter methods"""
        with app.app_context():
            movie = Movie(id=102, title='Test Movie 3')
            
            # Test setting genres
            genres_list = [{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}]
            movie.set_genres(genres_list)
            
            assert movie.get_genres() == genres_list
            
            # Test with string input
            movie.set_genres('[{"id": 35, "name": "Comedy"}]')
            genres = movie.get_genres()
            assert len(genres) == 1
            assert genres[0]['name'] == 'Comedy'
    
    def test_movie_production_countries_methods(self, app):
        """Test movie production countries getter/setter methods"""
        with app.app_context():
            movie = Movie(id=103, title='Test Movie 4')
            
            countries_list = ['US', 'GB', 'CA']
            movie.set_production_countries(countries_list)
            
            assert movie.get_production_countries() == countries_list
            
            # Test with string input
            movie.set_production_countries('["US", "JP"]')
            countries = movie.get_production_countries()
            assert countries == ['US', 'JP']
    
    def test_movie_keywords_methods(self, app):
        """Test movie keywords getter/setter methods"""
        with app.app_context():
            movie = Movie(id=104, title='Test Movie 5')
            
            keywords_list = ['action', 'adventure', 'thriller']
            movie.set_keywords(keywords_list)
            
            assert movie.get_keywords() == keywords_list
    
    def test_movie_from_csv_data(self, app):
        """Test creating movie from CSV data"""
        with app.app_context():
            csv_data = {
                'id': 105,
                'tmdb_id': 1005,
                'title': 'CSV Movie',
                'overview': 'CSV Overview',
                'release_date': '2023-03-01',
                'popularity': '70.5',
                'vote_average': '8.2',
                'vote_count': '1500',
                'runtime': '125',
                'poster_path': '/csv.jpg',
                'original_language': 'en',
                'director': 'CSV Director',
                'genres': '[{"id": 28, "name": "Action"}]',
                'production_countries': '["US", "GB"]'
            }
            
            movie = Movie.from_csv_data(csv_data)
            
            assert movie.id == 105
            assert movie.title == 'CSV Movie'
            assert movie.vote_average == 8.2
            assert movie.release_date == date(2023, 3, 1)
            assert movie.get_genres() == [{'id': 28, 'name': 'Action'}]
            assert movie.get_production_countries() == ['US', 'GB']
    
    def test_movie_from_csv_data_edge_cases(self, app):
        """Test movie from CSV data with edge cases"""
        with app.app_context():
            # Test with missing/invalid data
            csv_data = {
                'id': None,
                'title': '',
                'popularity': 'invalid',
                'vote_average': 'nan',
                'vote_count': '',
                'release_date': 'invalid_date',
                'genres': 'invalid_json',
                'production_countries': ''
            }
            
            movie = Movie.from_csv_data(csv_data)
            
            assert movie.id is None
            assert movie.title == ''
            assert movie.popularity == 0.0
            assert movie.vote_average == 0.0
            assert movie.vote_count == 0
            assert movie.release_date is None
            assert movie.get_genres() == []
            assert movie.get_production_countries() == []

class TestGenreModel:
    """Test Genre model"""
    
    def test_create_genre(self, app):
        """Test creating a genre"""
        with app.app_context():
            genre = Genre(
                tmdb_id=999,
                name='Test Genre',
                movie_count=10
            )
            
            db.session.add(genre)
            db.session.commit()
            
            retrieved_genre = Genre.query.filter_by(tmdb_id=999).first()
            assert retrieved_genre is not None
            assert retrieved_genre.name == 'Test Genre'
            assert retrieved_genre.movie_count == 10

class TestMovieRecommendationModel:
    """Test MovieRecommendation model"""
    
    def test_create_recommendation(self, app):
        """Test creating a movie recommendation"""
        with app.app_context():
            # Create movies first
            movie1 = Movie(id=200, title='Movie 1')
            movie2 = Movie(id=201, title='Movie 2')
            db.session.add(movie1)
            db.session.add(movie2)
            db.session.commit()
            
            # Create recommendation
            recommendation = MovieRecommendation(
                movie_id=200,
                recommended_movie_id=201,
                similarity_score=0.85,
                recommendation_type='hybrid'
            )
            
            db.session.add(recommendation)
            db.session.commit()
            
            retrieved_rec = MovieRecommendation.query.filter_by(
                movie_id=200, recommended_movie_id=201
            ).first()
            
            assert retrieved_rec is not None
            assert retrieved_rec.similarity_score == 0.85
            assert retrieved_rec.recommendation_type == 'hybrid'

class TestSearchCacheModel:
    """Test SearchCache model"""
    
    def test_create_search_cache(self, app):
        """Test creating search cache entry"""
        with app.app_context():
            cache_entry = SearchCache(
                query_hash='test_hash',
                query='test query',
                result_count=5,
                movie_ids='[1, 2, 3, 4, 5]',
                expires_at=datetime.utcnow()
            )
            
            db.session.add(cache_entry)
            db.session.commit()
            
            retrieved_cache = SearchCache.query.filter_by(query_hash='test_hash').first()
            assert retrieved_cache is not None
            assert retrieved_cache.query == 'test query'
            assert retrieved_cache.result_count == 5
    
    def test_search_cache_methods(self, app):
        """Test search cache getter/setter methods"""
        with app.app_context():
            cache_entry = SearchCache(
                query_hash='test_hash2',
                query='test query 2',
                expires_at=datetime.utcnow()
            )
            
            # Test movie IDs methods
            movie_ids = [1, 2, 3, 4, 5]
            cache_entry.set_movie_ids(movie_ids)
            assert cache_entry.get_movie_ids() == movie_ids
            
            # Test filters methods
            filters = {'genre': 'Action', 'year': '2023'}
            cache_entry.set_filters(filters)
            assert cache_entry.get_filters() == filters

class TestUserRatingModel:
    """Test UserRating model"""
    
    def test_create_user_rating(self, app):
        """Test creating a user rating"""
        with app.app_context():
            # Create movie first
            movie = Movie(id=300, title='Movie 300')
            db.session.add(movie)
            db.session.commit()
            
            # Create rating
            rating = UserRating(
                user_id='test_user_123',
                movie_id=300,
                rating=8.5
            )
            
            db.session.add(rating)
            db.session.commit()
            
            retrieved_rating = UserRating.query.filter_by(
                user_id='test_user_123', movie_id=300
            ).first()
            
            assert retrieved_rating is not None
            assert retrieved_rating.rating == 8.5

class TestModelRelationships:
    """Test model relationships"""
    
    def test_movie_recommendations_relationship(self, app):
        """Test movie-recommendations relationship"""
        with app.app_context():
            # Create movies
            movie1 = Movie(id=400, title='Movie 400')
            movie2 = Movie(id=401, title='Movie 401')
            movie3 = Movie(id=402, title='Movie 402')
            db.session.add_all([movie1, movie2, movie3])
            db.session.commit()
            
            # Create recommendations
            rec1 = MovieRecommendation(movie_id=400, recommended_movie_id=401, similarity_score=0.8)
            rec2 = MovieRecommendation(movie_id=400, recommended_movie_id=402, similarity_score=0.7)
            db.session.add_all([rec1, rec2])
            db.session.commit()
            
            # Test relationship
            movie = Movie.query.get(400)
            recommendations = movie.recommendations.all()
            
            assert len(recommendations) == 2
            assert recommendations[0].recommended_movie_id == 401
            assert recommendations[1].recommended_movie_id == 402
    
    def test_movie_user_ratings_relationship(self, app):
        """Test movie-user_ratings relationship"""
        with app.app_context():
            # Create movie
            movie = Movie(id=500, title='Movie 500')
            db.session.add(movie)
            db.session.commit()
            
            # Create ratings
            rating1 = UserRating(user_id='user1', movie_id=500, rating=8.0)
            rating2 = UserRating(user_id='user2', movie_id=500, rating=7.5)
            db.session.add_all([rating1, rating2])
            db.session.commit()
            
            # Test relationship
            movie = Movie.query.get(500)
            ratings = movie.user_ratings.all()
            
            assert len(ratings) == 2
            assert ratings[0].rating == 8.0
            assert ratings[1].rating == 7.5

class TestModelConstraints:
    """Test model constraints and validations"""
    
    def test_unique_constraints(self, app):
        """Test unique constraints"""
        with app.app_context():
            # Create first movie
            movie1 = Movie(id=600, title='Movie 600')
            db.session.add(movie1)
            db.session.commit()
            
            # Try to create movie with same ID (should fail)
            movie2 = Movie(id=600, title='Movie 600 Duplicate')
            db.session.add(movie2)
            
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()
    
    def test_nullable_constraints(self, app):
        """Test nullable constraints"""
        with app.app_context():
            # Movie with required fields only
            movie = Movie(id=601, title='Movie 601')
            db.session.add(movie)
            db.session.commit()
            
            retrieved_movie = Movie.query.get(601)
            assert retrieved_movie.title == 'Movie 601'
            assert retrieved_movie.overview is None  # Should be None
            assert retrieved_movie.director is None  # Should be None
