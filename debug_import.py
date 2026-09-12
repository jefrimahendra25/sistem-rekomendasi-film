import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.movie_service import movie_service
    print("SUCCESS: movie_service imported successfully")
    print(f"Service type: {type(movie_service)}")
    
    # Test loading movies
    movies = movie_service.load_movies()
    print(f"Movies loaded: {len(movies)}")
    
    # Test get_genres
    genres = movie_service.get_genres(movies)
    print(f"Genres found: {len(genres)}")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
