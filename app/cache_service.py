"""
Advanced caching service for performance optimization
"""
import json
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps
import flask
from .models import db, SearchCache

current_app = None

def _get_current_app():
    if current_app is not None:
        return current_app
    try:
        return flask.current_app
    except RuntimeError:
        return None

logger = logging.getLogger(__name__)

class CacheService:
    """Advanced caching service with Redis and database fallback"""
    
    def __init__(self):
        self.default_timeout = 300  # 5 minutes
        self.search_timeout = 600   # 10 minutes
        self.movie_timeout = 1800   # 30 minutes
        self.genre_timeout = 3600  # 1 hour
        self.stats_timeout = 300    # 5 minutes
    
    def get_cache_key(self, prefix, *args, **kwargs):
        """Generate consistent cache key"""
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key):
        """Get value from cache (Redis first, then database)"""
        try:
            # Try Redis first
            cache = getattr(_get_current_app(), 'cache', None)
            if cache:
                value = cache.get(key)
                if value is not None:
                    logger.debug(f"Cache hit (Redis): {key}")
                    return value
            
            # Try database cache for search results
            if key.startswith('search:'):
                return self._get_from_database_cache(key)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key, value, timeout=None):
        """Set value in cache (Redis and database for search)"""
        try:
            timeout = timeout or self.default_timeout
            
            # Set in Redis
            cache = getattr(_get_current_app(), 'cache', None)
            if cache:
                cache.set(key, value, timeout=timeout)
                logger.debug(f"Cache set (Redis): {key}")
            
            # Also store search results in database
            if key.startswith('search:'):
                self._set_database_cache(key, value, timeout)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        try:
            cache = getattr(_get_current_app(), 'cache', None)
            if cache:
                cache.delete(key)
            
            # Delete from database cache
            if key.startswith('search:'):
                db.session.query(SearchCache).filter_by(query_hash=key.replace('search:', '')).delete()
                db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """Clear cache keys matching pattern"""
        try:
            cache = getattr(_get_current_app(), 'cache', None)
            if cache and hasattr(cache, 'cache'):
                # For Redis cache
                if hasattr(cache.cache, 'keys'):
                    keys = cache.cache.keys(f"*{pattern}*")
                    if keys:
                        cache.cache.delete(*keys)
                        logger.info(f"Cleared {len(keys)} cache keys matching pattern: {pattern}")

            # Clear from database
            if 'search' in pattern:
                db.session.query(SearchCache).delete()
                db.session.commit()

        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
    
    def _get_from_database_cache(self, key):
        """Get search cache from database"""
        try:
            query_hash = key.replace('search:', '')
            cache_entry = SearchCache.query.filter_by(query_hash=query_hash).first()
            
            if cache_entry and cache_entry.expires_at > datetime.utcnow():
                return json.loads(cache_entry.movie_ids)
            elif cache_entry and cache_entry.expires_at <= datetime.utcnow():
                # Remove expired entry
                db.session.delete(cache_entry)
                db.session.commit()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from database cache: {e}")
            return None
    
    def _set_database_cache(self, key, value, timeout):
        """Set search cache in database"""
        try:
            if not isinstance(value, list):
                return
            
            query_hash = key.replace('search:', '')
            expires_at = datetime.utcnow() + timedelta(seconds=timeout)
            
            # Remove existing entry
            SearchCache.query.filter_by(query_hash=query_hash).delete()
            
            # Create new entry
            cache_entry = SearchCache(
                query_hash=query_hash,
                query=key.replace('search:', '').split('_')[0],  # Extract query from key
                result_count=len(value),
                movie_ids=json.dumps(value),
                expires_at=expires_at
            )
            
            db.session.add(cache_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error setting database cache: {e}")
            db.session.rollback()
    
    def cache_search_results(self, query, filters, movie_ids, timeout=None):
        """Cache search results with metadata"""
        try:
            timeout = timeout or self.search_timeout
            
            # Create cache key
            cache_key = self.get_cache_key('search', query, **filters)
            
            # Store in cache
            self.set(cache_key, movie_ids, timeout)
            
            # Also store in database with metadata
            query_hash = hashlib.md5(f"{query}_{json.dumps(filters, sort_keys=True)}".encode()).hexdigest()
            expires_at = datetime.utcnow() + timedelta(seconds=timeout)
            
            # Remove existing entry
            SearchCache.query.filter_by(query_hash=query_hash).delete()
            
            # Create new entry
            cache_entry = SearchCache(
                query_hash=query_hash,
                query=query,
                filters=json.dumps(filters),
                result_count=len(movie_ids),
                movie_ids=json.dumps(movie_ids),
                expires_at=expires_at
            )
            
            db.session.add(cache_entry)
            db.session.commit()
            
            logger.info(f"Cached search results for query: '{query}' ({len(movie_ids)} results)")
            
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
            db.session.rollback()
    
    def get_cached_search(self, query, filters):
        """Get cached search results"""
        try:
            # Try Redis first
            cache_key = self.get_cache_key('search', query, **filters)
            cached_ids = self.get(cache_key)
            
            if cached_ids:
                return cached_ids
            
            # Try database
            query_hash = hashlib.md5(f"{query}_{json.dumps(filters, sort_keys=True)}".encode()).hexdigest()
            cache_entry = SearchCache.query.filter_by(query_hash=query_hash).first()
            
            if cache_entry and cache_entry.expires_at > datetime.utcnow():
                logger.info(f"Database cache hit for search: '{query}'")
                return json.loads(cache_entry.movie_ids)
            elif cache_entry and cache_entry.expires_at <= datetime.utcnow():
                # Remove expired entry
                db.session.delete(cache_entry)
                db.session.commit()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached search: {e}")
            return None
    
    def cache_movie_recommendations(self, movie_id, recommendations, timeout=None):
        """Cache movie recommendations"""
        try:
            timeout = timeout or self.movie_timeout
            cache_key = f"movie_recommendations:{movie_id}"
            
            self.set(cache_key, recommendations, timeout)
            logger.info(f"Cached {len(recommendations)} recommendations for movie {movie_id}")
            
        except Exception as e:
            logger.error(f"Error caching movie recommendations: {e}")
    
    def get_cached_recommendations(self, movie_id):
        """Get cached movie recommendations"""
        try:
            cache_key = f"movie_recommendations:{movie_id}"
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached recommendations: {e}")
            return None
    
    def cache_genres(self, genres, timeout=None):
        """Cache genres list"""
        try:
            timeout = timeout or self.genre_timeout
            cache_key = "genres:list"
            
            self.set(cache_key, genres, timeout)
            logger.info(f"Cached {len(genres)} genres")
            
        except Exception as e:
            logger.error(f"Error caching genres: {e}")
    
    def get_cached_genres(self):
        """Get cached genres"""
        try:
            cache_key = "genres:list"
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached genres: {e}")
            return None
    
    def cache_stats(self, stats, timeout=None):
        """Cache database statistics"""
        try:
            timeout = timeout or self.stats_timeout
            cache_key = "database:stats"
            
            self.set(cache_key, stats, timeout)
            
        except Exception as e:
            logger.error(f"Error caching stats: {e}")
    
    def get_cached_stats(self):
        """Get cached statistics"""
        try:
            cache_key = "database:stats"
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached stats: {e}")
            return None
    
    def invalidate_movie_cache(self, movie_id=None):
        """Invalidate movie-related cache"""
        try:
            if movie_id:
                # Invalidate specific movie cache
                patterns = [
                    f"movie:{movie_id}",
                    f"movie_recommendations:{movie_id}",
                    f"movies:*_{movie_id}_*"  # Movie lists containing this movie
                ]
            else:
                # Invalidate all movie cache
                patterns = ["movie:", "movies:", "movie_recommendations:"]
            
            for pattern in patterns:
                self.clear_pattern(pattern)
            
            logger.info(f"Invalidated movie cache for movie_id: {movie_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating movie cache: {e}")
    
    def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            # Clean up database cache
            expired_count = SearchCache.query.filter(
                SearchCache.expires_at < datetime.utcnow()
            ).delete()
            
            db.session.commit()
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired database cache entries")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0
    
    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            stats = {
                'database_cache_entries': SearchCache.query.count(),
                'expired_entries': SearchCache.query.filter(
                    SearchCache.expires_at < datetime.utcnow()
                ).count(),
                'redis_available': False,
                'cache_hit_rate': 0.0
            }
            
            # Check Redis availability
            cache = getattr(current_app, 'cache', None)
            if cache:
                stats['redis_available'] = True
                # Note: Getting hit rate from Redis would require additional monitoring
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


# Decorators for easy caching
def cache_result(timeout=300, key_prefix=None):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_service = CacheService()
            
            # Generate cache key
            prefix = key_prefix or f"function:{f.__name__}"
            cache_key = cache_service.get_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache_service.set(cache_key, result, timeout)
            
            return result
        
        return decorated_function
    return decorator


def cache_search(timeout=600):
    """Decorator specifically for search functions"""
    return cache_result(timeout=timeout, key_prefix='search')


def cache_movie(timeout=1800):
    """Decorator specifically for movie functions"""
    return cache_result(timeout=timeout, key_prefix='movie')


# Create global instance
cache_service = CacheService()
