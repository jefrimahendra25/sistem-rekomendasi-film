"""
Database initialization and migration utilities
"""
import os
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import text
from .models import db, Movie, MovieRecommendation, SearchCache, Genre, UserRating
from .utils import clean_poster_path

logger = logging.getLogger(__name__)

def init_database(app):
    """Initialize database with tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Check if we need to import data
            if Movie.query.count() == 0:
                logger.info("Database is empty, importing CSV data...")
                import_csv_data()
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            return False

def import_csv_data():
    """Import data from CSV files to database"""
    try:
        from .utils import get_data_file_path
        
        csv_path = get_data_file_path()
        logger.info(f"Importing data from: {csv_path}")
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        # Read CSV with pandas
        try:
            df = pd.read_csv(csv_path, delimiter=';', encoding='utf-8', on_bad_lines='warn')
        except Exception:
            try:
                df = pd.read_csv(csv_path, delimiter=',', encoding='utf-8', on_bad_lines='warn')
            except Exception as e:
                logger.error(f"Failed to read CSV file: {e}")
                return False
        
        if df.empty:
            logger.error("CSV file is empty")
            return False
        
        logger.info(f"Found {len(df)} records in CSV file")
        
        # Import movies in batches
        batch_size = 100
        imported_count = 0
        failed_count = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                try:
                    # Convert row to dictionary
                    movie_data = row.to_dict()
                    
                    # Clean and validate data
                    movie_data = clean_movie_data(movie_data)
                    
                    # Create Movie instance
                    movie = Movie.from_csv_data(movie_data)
                    
                    # Check if movie already exists
                    existing_movie = Movie.query.filter_by(id=movie.id).first()
                    if existing_movie:
                        # Update existing movie
                        for key, value in movie_data.items():
                            if hasattr(existing_movie, key):
                                setattr(existing_movie, key, value)
                        existing_movie.updated_at = datetime.utcnow()
                    else:
                        # Add new movie
                        db.session.add(movie)
                    
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import movie {row.get('id', 'unknown')}: {e}")
                    failed_count += 1
                    continue
            
            # Commit batch
            try:
                db.session.commit()
                logger.info(f"Imported batch {i//batch_size + 1}: {imported_count} movies")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to commit batch: {e}")
                failed_count += batch_size
        
        logger.info(f"Data import completed: {imported_count} imported, {failed_count} failed")
        
        # Update genre statistics
        update_genre_statistics()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to import CSV data: {str(e)}")
        db.session.rollback()
        return False

def clean_movie_data(movie_data):
    """Clean and validate movie data"""
    # Clean poster path
    if 'poster_path' in movie_data:
        movie_data['poster_path'] = clean_poster_path(movie_data['poster_path'])
    
    # Handle numeric fields
    for field in ['popularity', 'vote_average', 'vote_count', 'runtime']:
        if field in movie_data:
            try:
                value = movie_data[field]
                if pd.isna(value) or value in ['', 'nan', 'None']:
                    movie_data[field] = 0
                else:
                    movie_data[field] = float(str(value).replace(',', ''))
            except (ValueError, TypeError):
                movie_data[field] = 0
    
    # Handle ID field
    if 'id' in movie_data:
        try:
            movie_data['id'] = int(movie_data['id'])
        except (ValueError, TypeError):
            movie_data['id'] = None
    
    # Handle genres
    if 'genres' in movie_data:
        genres = movie_data['genres']
        if isinstance(genres, str):
            try:
                if genres.startswith('[') and genres.endswith(']'):
                    genres = json.loads(genres)
                else:
                    genres = [g.strip() for g in genres.split(',') if g.strip()]
            except:
                genres = []
        movie_data['genres'] = genres
    
    # Handle production countries
    if 'production_countries' in movie_data:
        countries = movie_data['production_countries']
        if isinstance(countries, str):
            try:
                if countries.startswith('[') and countries.endswith(']'):
                    countries = json.loads(countries)
                else:
                    countries = [c.strip() for c in countries.split(',') if c.strip()]
            except:
                countries = []
        movie_data['production_countries'] = countries
    
    return movie_data

def update_genre_statistics():
    """Update genre statistics in the database"""
    try:
        logger.info("Updating genre statistics...")
        
        # Get all movies and count genres
        movies = Movie.query.all()
        genre_counts = {}
        
        for movie in movies:
            genres = movie.get_genres()
            for genre in genres:
                if isinstance(genre, dict):
                    genre_name = genre.get('name', '')
                else:
                    genre_name = str(genre)
                
                if genre_name:
                    genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1
        
        # Update or create genre records
        for genre_name, count in genre_counts.items():
            genre = Genre.query.filter_by(name=genre_name).first()
            if genre:
                genre.movie_count = count
                genre.updated_at = datetime.utcnow()
            else:
                # Create new genre (we'll use a simple ID generation)
                genre = Genre(
                    tmdb_id=hash(genre_name) % 100000,  # Simple hash for ID
                    name=genre_name,
                    movie_count=count
                )
                db.session.add(genre)
        
        db.session.commit()
        logger.info(f"Updated {len(genre_counts)} genres")
        
    except Exception as e:
        logger.error(f"Failed to update genre statistics: {e}")
        db.session.rollback()

def cleanup_expired_cache():
    """Clean up expired search cache entries"""
    try:
        expired_count = db.session.query(SearchCache).filter(
            SearchCache.expires_at < datetime.utcnow()
        ).delete()
        
        db.session.commit()
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired cache entries")
        
        return expired_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired cache: {e}")
        db.session.rollback()
        return 0

def get_database_stats():
    """Get database statistics"""
    try:
        stats = {
            'movies': Movie.query.count(),
            'recommendations': MovieRecommendation.query.count(),
            'genres': Genre.query.count(),
            'search_cache': db.session.query(SearchCache).count(),
            'user_ratings': UserRating.query.count(),
            'latest_movie': None,
            'oldest_movie': None
        }
        
        # Get date range
        if stats['movies'] > 0:
            latest = Movie.query.order_by(Movie.release_date.desc()).first()
            oldest = Movie.query.order_by(Movie.release_date.asc()).first()
            
            stats['latest_movie'] = latest.release_date.isoformat() if latest and latest.release_date else None
            stats['oldest_movie'] = oldest.release_date.isoformat() if oldest and oldest.release_date else None
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}

def backup_database():
    """Create a simple backup of the database (SQLite only)"""
    try:
        database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        if database_url.startswith('sqlite:///'):
            # For SQLite, create a copy of the database file
            db_path = database_url.replace('sqlite:///', '')
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            import shutil
            shutil.copy2(db_path, backup_path)
            
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        else:
            logger.warning("Database backup only supported for SQLite")
            return None
            
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None

def optimize_database():
    """Run database optimization commands"""
    try:
        # For SQLite
        if current_app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite:///'):
            db.session.execute(text('VACUUM'))
            db.session.execute(text('ANALYZE'))
            db.session.commit()
            logger.info("Database optimized (SQLite)")
        
        # For PostgreSQL (if used in production)
        elif 'postgresql' in current_app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            db.session.execute(text('VACUUM ANALYZE'))
            db.session.commit()
            logger.info("Database optimized (PostgreSQL)")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to optimize database: {e}")
        return False
