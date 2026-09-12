"""
Database models for the movie recommendation application
"""
from datetime import datetime
from sqlalchemy import Index, text
from sqlalchemy import desc
from sqlalchemy.orm import aliased
import json
import math

# IMPORTANT: use the shared SQLAlchemy instance from app.__init__
from . import db

class Movie(db.Model):
    """Movie model for storing movie data"""
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=True, index=True)
    title = db.Column(db.String(500), nullable=False, index=True)
    original_title = db.Column(db.String(500))
    overview = db.Column(db.Text)
    release_date = db.Column(db.Date, index=True)
    popularity = db.Column(db.Float, default=0.0, index=True)
    vote_average = db.Column(db.Float, default=0.0, index=True)
    vote_count = db.Column(db.Integer, default=0, index=True)
    poster_path = db.Column(db.String(500))
    backdrop_path = db.Column(db.String(500))
    original_language = db.Column(db.String(10), default='en', index=True)
    runtime = db.Column(db.Integer)
    director = db.Column(db.String(200))
    production_countries = db.Column(db.Text)  # JSON string
    genres = db.Column(db.Text)  # JSON string
    keywords = db.Column(db.Text)  # JSON string for search optimization
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recommendations = db.relationship(
        'MovieRecommendation',
        foreign_keys='MovieRecommendation.movie_id',
        backref='movie',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by="desc(MovieRecommendation.similarity_score)"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_movie_title_release', 'title', 'release_date'),
        Index('idx_movie_popularity_rating', 'popularity', 'vote_average'),
        Index('idx_movie_language_date', 'original_language', 'release_date'),
    )
    
    def to_dict(self):
        """Convert movie object to dictionary"""
        return {
            'id': self.id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'original_title': self.original_title,
            'overview': self.overview,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'popularity': self.popularity,
            'vote_average': self.vote_average,
            'vote_count': self.vote_count,
            'poster_path': self.poster_path,
            'backdrop_path': self.backdrop_path,
            'original_language': self.original_language,
            'runtime': self.runtime,
            'director': self.director,
            'production_countries': self.get_production_countries(),
            'genres': self.get_genres(),
            'keywords': self.get_keywords(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_genres(self):
        """Parse genres JSON string to list"""
        if self.genres:
            try:
                return json.loads(self.genres)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_genres(self, genres_list):
        """Set genres from list"""
        try:
            if isinstance(genres_list, str):
                parsed = json.loads(genres_list)
                if isinstance(parsed, list):
                    self.genres = json.dumps(parsed)
                    return
            if isinstance(genres_list, list):
                self.genres = json.dumps(genres_list)
                return
        except Exception:
            pass
        # Fallback empty list
        self.genres = json.dumps([])
    
    def get_production_countries(self):
        """Parse production countries JSON string to list"""
        if self.production_countries:
            try:
                return json.loads(self.production_countries)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_production_countries(self, countries_list):
        """Set production countries from list"""
        try:
            if isinstance(countries_list, str):
                parsed = json.loads(countries_list)
                if isinstance(parsed, list):
                    self.production_countries = json.dumps(parsed)
                    return
            if isinstance(countries_list, list):
                self.production_countries = json.dumps(countries_list)
                return
        except Exception:
            pass
        self.production_countries = json.dumps([])
    
    def get_keywords(self):
        """Parse keywords JSON string to list"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_keywords(self, keywords_list):
        """Set keywords from list"""
        if isinstance(keywords_list, list):
            self.keywords = json.dumps(keywords_list)
        else:
            self.keywords = json.dumps([])
    
    @classmethod
    def from_csv_data(cls, csv_data):
        """Create Movie instance from CSV data"""
        movie = cls()
        
        # Basic fields
        movie.id = csv_data.get('id')
        movie.tmdb_id = csv_data.get('tmdb_id') or csv_data.get('id')
        movie.title = csv_data.get('title', '')
        movie.original_title = csv_data.get('original_title', '')
        movie.overview = csv_data.get('overview', '')
        
        # Date handling
        release_date = csv_data.get('release_date')
        if release_date and release_date not in ['nan', 'None', '']:
            try:
                movie.release_date = datetime.strptime(release_date, '%Y-%m-%d').date()
            except ValueError:
                movie.release_date = None
        else:
            movie.release_date = None
        
        # Numeric fields
        # Safe numeric conversions with fallbacks
        try:
            movie.popularity = float(str(csv_data.get('popularity', 0) or 0).replace(',', '.'))
        except Exception:
            movie.popularity = 0.0
        try:
            va = float(str(csv_data.get('vote_average', 0) or 0).replace(',', '.'))
            if math.isnan(va):
                movie.vote_average = 0.0
            else:
                movie.vote_average = va
        except Exception:
            movie.vote_average = 0.0
        try:
            movie.vote_count = int(float(str(csv_data.get('vote_count', 0) or 0)))
        except Exception:
            movie.vote_count = 0
        movie.runtime = int(csv_data.get('runtime', 0) or 0)
        
        # String fields
        movie.poster_path = csv_data.get('poster_path', '')
        movie.backdrop_path = csv_data.get('backdrop_path', '')
        movie.original_language = csv_data.get('original_language', 'en')
        movie.director = csv_data.get('director', '')
        
        # JSON fields
        genres = csv_data.get('genres', [])
        if isinstance(genres, str):
            try:
                genres = json.loads(genres)
            except:
                genres = []
        movie.set_genres(genres)
        
        countries = csv_data.get('production_countries', [])
        if isinstance(countries, str):
            try:
                countries = json.loads(countries)
            except:
                countries = []
        movie.set_production_countries(countries)
        
        # Generate keywords for search optimization
        keywords = []
        if movie.title:
            keywords.extend(movie.title.lower().split())
        if movie.overview:
            keywords.extend(movie.overview.lower().split()[:20])  # Limit overview keywords
        if movie.director:
            keywords.append(movie.director.lower())
        
        # Add genre names as keywords
        for genre in movie.get_genres():
            if isinstance(genre, dict):
                keywords.append(genre.get('name', '').lower())
            else:
                keywords.append(str(genre).lower())
        
        movie.set_keywords(list(set(keywords)))  # Remove duplicates
        
        return movie


class MovieRecommendation(db.Model):
    """Movie recommendations model"""
    __tablename__ = 'movie_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    recommended_movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    similarity_score = db.Column(db.Float, default=0.0)
    recommendation_type = db.Column(db.String(50), default='hybrid')  # hybrid, genre, tfidf
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recommended_movie = db.relationship('Movie', foreign_keys=[recommended_movie_id], backref='recommended_by')
    
    # Indexes
    __table_args__ = (
        Index('idx_recommendation_movie_score', 'movie_id', 'similarity_score'),
        Index('idx_recommendation_type', 'recommendation_type'),
    )


class SearchCache(db.Model):
    """Search cache model for performance optimization"""
    __tablename__ = 'search_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    query_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    # Use attribute name `query_text` mapped to DB column `query` to avoid
    # shadowing the common `query` Query property. Provide an initializer
    # and a class-level descriptor so tests can use `SearchCache.query.filter_by(...)`.
    query_text = db.Column('query', db.String(500), nullable=False)
    filters = db.Column(db.Text)  # JSON string for filters
    result_count = db.Column(db.Integer, default=0)
    movie_ids = db.Column(db.Text)  # JSON array of movie IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    def set_movie_ids(self, movie_ids_list):
        """Set movie IDs from list"""
        if isinstance(movie_ids_list, list):
            self.movie_ids = json.dumps(movie_ids_list)
        else:
            self.movie_ids = json.dumps([])
    
    def get_movie_ids(self):
        """Get movie IDs as list"""
        if self.movie_ids:
            try:
                return json.loads(self.movie_ids)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_filters(self, filters_dict):
        """Set filters from dictionary"""
        if isinstance(filters_dict, dict):
            self.filters = json.dumps(filters_dict)
        else:
            self.filters = json.dumps({})
    
    def get_filters(self):
        """Get filters as dictionary"""
        if self.filters:
            try:
                return json.loads(self.filters)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def __init__(self, *args, **kwargs):
        # Accept `query` kw for compatibility with tests, map to `query_text`.
        q = kwargs.pop('query', None)
        super().__init__(*args, **kwargs)
        if q is not None:
            self.query_text = q

    # Descriptor to expose a class-level `query` that returns a session Query
    class _QueryDescriptor:
        def __get__(self, instance, owner):
            if instance is None:
                return db.session.query(owner)
            return instance.query_text

    query = _QueryDescriptor()


class Genre(db.Model):
    """Genre model for caching genre information"""
    __tablename__ = 'genres'
    
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False, index=True)
    movie_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserRating(db.Model):
    """User ratings model for future recommendation improvements"""
    __tablename__ = 'user_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)  # Anonymous user ID
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)  # 1-10 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    movie = db.relationship('Movie', backref=db.backref('user_ratings', lazy='dynamic', order_by='UserRating.id'))
    
    # Indexes
    __table_args__ = (
        Index('idx_user_rating_user', 'user_id', 'movie_id'),
        Index('idx_user_rating_movie', 'movie_id', 'rating'),
    )
