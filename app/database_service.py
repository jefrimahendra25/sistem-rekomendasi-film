"""
Database service for optimized movie operations
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, asc, func, case
from flask import current_app
from .models import db, Movie, MovieRecommendation, SearchCache, Genre
from .utils import validate_pagination_params, validate_movie_filters, paginate_movies

logger = logging.getLogger(__name__)

class DatabaseMovieService:
    """Optimized movie service using database"""
    
    def __init__(self):
        self._cache_timeout = 3600  # 1 hour
    
    def get_movies(self, movie_type='trending', genre_id='', year='', page=1, show_all=False):
        """Get movies with filters and sorting from database"""
        try:
            # Build query
            query = Movie.query
            
            # Apply filters
            if genre_id:
                query = self._apply_genre_filter(query, genre_id)
            
            if year:
                query = query.filter(
                    func.strftime('%Y', Movie.release_date) == str(year)
                )
            
            # Apply sorting
            query = self._apply_sorting(query, movie_type)
            
            # Execute query
            if show_all:
                movies = query.all()
            else:
                page, _ = validate_pagination_params(page)
                per_page = 20
                pagination = query.paginate(
                    page=page, per_page=per_page, error_out=False
                )
                movies = pagination.items
                total_pages = pagination.pages
                total_movies = pagination.total
            
            # Convert to dict format
            movie_list = [movie.to_dict() for movie in movies]
            
            if show_all:
                return movie_list, page, 1, len(movie_list)
            else:
                return movie_list, page, total_pages, total_movies
                
        except Exception as e:
            logger.error(f"Error getting movies from database: {e}")
            return [], page, 1, 0
    
    def _apply_genre_filter(self, query, genre_id):
        """Apply genre filter to query"""
        try:
            # Try to find genre by name or ID
            genre = Genre.query.filter(
                or_(
                    Genre.name.ilike(f'%{genre_id}%'),
                    Genre.tmdb_id == int(genre_id) if genre_id.isdigit() else False
                )
            ).first()
            
            if genre:
                # Filter movies that contain this genre in their genres JSON
                query = query.filter(
                    Movie.genres.ilike(f'%{genre.name}%')
                )
            else:
                # Direct text search in genres field
                query = query.filter(Movie.genres.ilike(f'%{genre_id}%'))
            
            return query
            
        except Exception as e:
            logger.warning(f"Error applying genre filter: {e}")
            return query
    
    def _apply_sorting(self, query, movie_type):
        """Apply sorting to query"""
        if movie_type == 'trending':
            # Trending: Engagement Score + Recency Bonus (rumus skripsi)
            # Engagement Score = (vote_average * vote_count) / 1000
            # Recency Bonus = (30 - days_since_release) * 0.1 (jika ≤ 30 hari)
            # Karena SQL tidak bisa menghitung rumus kompleks, gunakan popularity sebagai fallback
            # atau perlu implementasi di application layer
            query = query.order_by(desc(Movie.popularity), desc(Movie.vote_count))
        elif movie_type == 'newest':
            query = query.order_by(desc(Movie.release_date))
        elif movie_type == 'popular':
            query = query.order_by(desc(Movie.vote_average), desc(Movie.vote_count))
        else:
            # Default: by rating
            query = query.order_by(desc(Movie.vote_average))
        
        return query
    
    def get_movie_by_id(self, movie_id):
        """Get movie by ID from database"""
        try:
            movie = Movie.query.filter_by(id=movie_id).first()
            return movie.to_dict() if movie else None
        except Exception as e:
            logger.error(f"Error getting movie by ID {movie_id}: {e}")
            return None
    
    def search_movies(self, query, page=None, show_all=False):
        """Search movies using database full-text search"""
        try:
            explicit_page = page is not None
            cache_key = f"search_{hash(query)}_{page}_{show_all}"
            cache = current_app.cache if hasattr(current_app, 'cache') else None
            
            if cache:
                cached_result = cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Build search query
            search_terms = query.lower().split()
            
            # Search in title, overview, director, and keywords
            conditions = []
            for term in search_terms:
                term_condition = or_(
                    Movie.title.ilike(f'%{term}%'),
                    Movie.overview.ilike(f'%{term}%'),
                    Movie.director.ilike(f'%{term}%'),
                    Movie.keywords.ilike(f'%{term}%')
                )
                conditions.append(term_condition)
            
            # Combine all conditions with AND
            if conditions:
                search_condition = and_(*conditions)
            else:
                search_condition = Movie.title.ilike(f'%{query}%')
            
            # Execute search
            search_query = Movie.query.filter(search_condition)
            search_query = search_query.order_by(
                # Prioritize exact title matches
                case(
                    (Movie.title.ilike(f'%{query}%'), 1),
                    else_=2
                ),
                desc(Movie.popularity),
                desc(Movie.vote_count)
            )
            
            if show_all:
                movies = search_query.all()
                movie_list = [movie.to_dict() for movie in movies]
                return movie_list

            page, _ = validate_pagination_params(page if page is not None else 1)
            per_page = 20
            pagination = search_query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            movies = pagination.items
            movie_list = [movie.to_dict() for movie in movies]

            if explicit_page:
                return movie_list, page, pagination.pages, pagination.total
            return movie_list
                
        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            return [] if show_all else ([], page, 1, 0)
    
    def get_genres(self):
        """Get all genres from database"""
        try:
            genres = Genre.query.order_by(Genre.name).all()
            return [
                {
                    'id': genre.tmdb_id,
                    'name': genre.name,
                    'count': genre.movie_count
                }
                for genre in genres
            ]
        except Exception as e:
            logger.error(f"Error getting genres: {e}")
            return []
    
    def get_recommendations(self, movie_id, top_n=10):
        """Get movie recommendations from database"""
        try:
            # Get cached recommendations first
            recommendations = MovieRecommendation.query.filter_by(
                movie_id=movie_id
            ).order_by(desc(MovieRecommendation.similarity_score)).limit(top_n).all()
            
            if recommendations:
                movie_ids = [rec.recommended_movie_id for rec in recommendations]
                movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()
                
                # Create movie lookup dict
                movie_dict = {movie.id: movie.to_dict() for movie in movies}
                
                # Return recommendations with scores
                result = []
                for rec in recommendations:
                    movie_data = movie_dict.get(rec.recommended_movie_id)
                    if movie_data:
                        movie_data['similarity_score'] = rec.similarity_score
                        movie_data['recommendation_type'] = rec.recommendation_type
                        result.append(movie_data)
                
                return result
            
            # If no cached recommendations, fall back to simple similarity
            return self._get_simple_recommendations(movie_id, top_n)
            
        except Exception as e:
            logger.error(f"Error getting recommendations for movie {movie_id}: {e}")
            return []
    
    def _get_simple_recommendations(self, movie_id, top_n=10):
        """Get simple recommendations based on genre similarity"""
        try:
            movie = Movie.query.filter_by(id=movie_id).first()
            if not movie:
                return []
            
            # Get movies with similar genres
            movie_genres = movie.get_genres()
            genre_names = []
            
            for genre in movie_genres:
                if isinstance(genre, dict):
                    genre_names.append(genre.get('name', '').lower())
                else:
                    genre_names.append(str(genre).lower())
            
            # Find movies with matching genres
            recommendations = []
            all_movies = Movie.query.filter(Movie.id != movie_id).limit(100).all()
            
            for other_movie in all_movies:
                other_genres = other_movie.get_genres()
                other_genre_names = []
                
                for genre in other_genres:
                    if isinstance(genre, dict):
                        other_genre_names.append(genre.get('name', '').lower())
                    else:
                        other_genre_names.append(str(genre).lower())
                
                # Calculate genre similarity
                common_genres = set(genre_names) & set(other_genre_names)
                if common_genres:
                    similarity = len(common_genres) / max(len(genre_names), len(other_genre_names))
                    if similarity > 0.3:  # Minimum 30% similarity
                        movie_data = other_movie.to_dict()
                        movie_data['similarity_score'] = similarity
                        movie_data['recommendation_type'] = 'genre'
                        recommendations.append(movie_data)
            
            # Sort by similarity and return top N
            recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
            return recommendations[:top_n]
            
        except Exception as e:
            logger.error(f"Error getting simple recommendations: {e}")
            return []
    
    def cache_recommendations(self, movie_id, recommendations, recommendation_type='hybrid'):
        """Cache recommendations in database"""
        try:
            # Clear existing recommendations for this movie
            MovieRecommendation.query.filter_by(movie_id=movie_id).delete()
            
            # Add new recommendations
            for rec_data in recommendations:
                recommendation = MovieRecommendation(
                    movie_id=movie_id,
                    recommended_movie_id=rec_data.get('id'),
                    similarity_score=rec_data.get('similarity_score', 0.0),
                    recommendation_type=recommendation_type
                )
                db.session.add(recommendation)
            
            db.session.commit()
            logger.info(f"Cached {len(recommendations)} recommendations for movie {movie_id}")
            
        except Exception as e:
            logger.error(f"Error caching recommendations: {e}")
            db.session.rollback()
    
    def get_stats(self):
        """Get database statistics"""
        try:
            stats = {
                'total_movies': Movie.query.count(),
                'total_genres': Genre.query.count(),
                'cached_recommendations': MovieRecommendation.query.count(),
                'cached_searches': db.session.query(SearchCache).count(),
                'latest_release': None,
                'oldest_release': None,
                'avg_rating': 0.0,
                'avg_vote_count': 0.0
            }
            
            # Get date range
            if stats['total_movies'] > 0:
                latest = Movie.query.order_by(desc(Movie.release_date)).first()
                oldest = Movie.query.order_by(asc(Movie.release_date)).first()
                
                stats['latest_release'] = latest.release_date.isoformat() if latest and latest.release_date else None
                stats['oldest_release'] = oldest.release_date.isoformat() if oldest and oldest.release_date else None
                
                # Get averages
                avg_stats = Movie.query.with_entities(
                    func.avg(Movie.vote_average),
                    func.avg(Movie.vote_count)
                ).first()
                
                stats['avg_rating'] = float(avg_stats[0] or 0.0)
                stats['avg_vote_count'] = float(avg_stats[1] or 0.0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

# Create global instance
database_movie_service = DatabaseMovieService()
