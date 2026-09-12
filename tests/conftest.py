"""
Pytest configuration and fixtures
"""
import pytest
import tempfile
import os
from datetime import datetime

from flask import Flask
from app import create_app
from app.models import db, Movie, Genre, MovieRecommendation
from app.database_service import database_movie_service
from app.cache_service import cache_service

@pytest.fixture
def app():
    """Create and configure a test app."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Set test configuration
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_DEBUG'] = 'False'
    os.environ['CACHE_TYPE'] = 'simple'  # Use simple cache for testing
    os.environ['RATELIMIT_DEFAULT'] = '1000 per day'  # High limit for testing
    
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        # Add test data
        _create_test_data()
        
        yield app
        
        # Cleanup
        db.drop_all()
        # Ensure SQLAlchemy closes any open connections before removing the DB file
        try:
            db.session.remove()
        except Exception:
            pass
        os.close(db_fd)
        try:
            os.unlink(db_path)
        except PermissionError:
            # On Windows the SQLite file can still be held by a connection.
            # Best-effort retry.
            import time
            time.sleep(0.2)
            try:
                os.unlink(db_path)
            except PermissionError:
                pass


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
    }

def _create_test_data():
    """Create test data for the database."""
    # Create test genres
    genres = [
        Genre(tmdb_id=28, name='Action', movie_count=2),
        Genre(tmdb_id=12, name='Adventure', movie_count=2),
        Genre(tmdb_id=35, name='Comedy', movie_count=1),
        Genre(tmdb_id=18, name='Drama', movie_count=1)
    ]
    
    for genre in genres:
        db.session.add(genre)
    
    # Create test movies
    movies = [
        Movie(
            id=1,
            tmdb_id=550,
            title='Fight Club',
            original_title='Fight Club',
            overview='An insomniac office worker and a devil-may-care soapmaker form an underground fight club...',
release_date=datetime.strptime('1999-10-15', '%Y-%m-%d').date(),
            popularity=50.0,
            vote_average=8.8,
            vote_count=20000,
            poster_path='/pB8BMNpdE6dRXec4YZEB2l4Y7sK.jpg',
            original_language='en',
            runtime=139,
            director='David Fincher',
            genres='[{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}]',
            keywords='fight club insomniac office worker underground'
        ),
        Movie(
            id=2,
            tmdb_id=13,
            title='Forrest Gump',
            original_title='Forrest Gump',
            overview='The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events...',
            release_date=datetime.strptime('1994-07-06', '%Y-%m-%d').date(),
            popularity=45.0,
            vote_average=8.8,
            vote_count=25000,
            poster_path='/arw2vcBveWOVZr13pxDpjsdSxBj.jpg',
            original_language='en',
            runtime=142,
            director='Robert Zemeckis',
            genres='[{"id": 18, "name": "Drama"}, {"id": 10749, "name": "Romance"}]',
            keywords='forrest gump vietnam war historical events'
        ),
        Movie(
            id=3,
            tmdb_id=157336,
            title='Interstellar',
            original_title='Interstellar',
            overview='A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
            release_date=datetime.strptime('2014-11-07', '%Y-%m-%d').date(),
            popularity=60.0,
            vote_average=8.6,
            vote_count=30000,
            poster_path='/gEU2QniE6E77NI6lBJ6c3gSp3Sx.jpg',
            original_language='en',
            runtime=169,
            director='Christopher Nolan',
            genres='[{"id": 12, "name": "Adventure"}, {"id": 18, "name": "Drama"}, {"id": 878, "name": "Science Fiction"}]',
            keywords='interstellar wormhole space humanity survival'
        ),
        Movie(
            id=4,
            tmdb_id=299536,
            title='Avengers: Infinity War',
            original_title='Avengers: Infinity War',
            overview='The Avengers and their allies must be willing to sacrifice all in an attempt to defeat the powerful Thanos.',
            release_date=datetime.strptime('2018-04-27', '%Y-%m-%d').date(),
            popularity=70.0,
            vote_average=8.4,
            vote_count=35000,
            poster_path='/7WsyChQLEftFiDOVTGdw3zYWsp9.jpg',
            original_language='en',
            runtime=149,
            director='Anthony Russo, Joe Russo',
            genres='[{"id": 12, "name": "Adventure"}, {"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}]',
            keywords='avengers infinity war thanos sacrifice'
        ),
        Movie(
            id=5,
            tmdb_id=24428,
            title='The Avengers',
            original_title='The Avengers',
            overview='Earth\'s mightiest heroes must come together and learn to fight as a team if they are going to stop the mischievous Loki...',
            release_date=datetime.strptime('2012-05-04', '%Y-%m-%d').date(),
            popularity=55.0,
            vote_average=8.0,
            vote_count=22000,
            poster_path='/cezWGskPY5x7GaglTTRN4Fagap9.jpg',
            original_language='en',
            runtime=143,
            director='Joss Whedon',
            genres='[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}, {"id": 878, "name": "Science Fiction"}]',
            keywords='avengers loki earth heroes team'
        )
    ]
    
    for movie in movies:
        db.session.add(movie)
    
    # Create test recommendations
    recommendations = [
        MovieRecommendation(
            movie_id=1,
            recommended_movie_id=2,
            similarity_score=0.85,
            recommendation_type='hybrid'
        ),
        MovieRecommendation(
            movie_id=1,
            recommended_movie_id=3,
            similarity_score=0.75,
            recommendation_type='genre'
        ),
        MovieRecommendation(
            movie_id=4,
            recommended_movie_id=5,
            similarity_score=0.90,
            recommendation_type='hybrid'
        )
    ]
    
    for rec in recommendations:
        db.session.add(rec)
    
    db.session.commit()

@pytest.fixture
def sample_movies():
    """Sample movie data for testing."""
    return [
        {
            'id': 1,
            'title': 'Test Movie 1',
            'overview': 'This is a test movie',
            'vote_average': 8.5,
            'vote_count': 1000,
            'genres': [{'id': 28, 'name': 'Action'}],
            'release_date': '2023-01-01'
        },
        {
            'id': 2,
            'title': 'Test Movie 2',
            'overview': 'Another test movie',
            'vote_average': 7.5,
            'vote_count': 500,
            'genres': [{'id': 35, 'name': 'Comedy'}],
            'release_date': '2023-02-01'
        }
    ]

@pytest.fixture
def mock_cache():
    """Mock cache service for testing."""
    class MockCache:
        def __init__(self):
            self.cache = {}
        
        def get(self, key):
            return self.cache.get(key)
        
        def set(self, key, value, timeout=None):
            self.cache[key] = value
            return True
        
        def delete(self, key):
            return self.cache.pop(key, None) is not None
        
        def clear(self):
            self.cache.clear()
    
    return MockCache()

@pytest.fixture
def sample_search_query():
    """Sample search query for testing."""
    return "avengers"

@pytest.fixture
def sample_genre_filter():
    """Sample genre filter for testing."""
    return "28"  # Action genre ID
