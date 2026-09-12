import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.movie_service import MovieService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_genres():
    try:
        print("=== DEBUG GENRES LOADING ===")
        
        # Initialize movie service
        movie_service = MovieService()
        
        # Load movies
        print("1. Loading movies...")
        movies = movie_service.load_movies()
        print(f"   Loaded {len(movies)} movies")
        
        if not movies:
            print("   ERROR: No movies loaded!")
            return
        
        # Test get_genres
        print("2. Getting genres...")
        genres = movie_service.get_genres(movies)
        print(f"   Found {len(genres)} genres")
        
        # Print first few genres
        print("3. Sample genres:")
        for i, genre in enumerate(genres[:5]):
            print(f"   {i+1}. {genre}")
            
        print("=== SUCCESS ===")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_genres()
