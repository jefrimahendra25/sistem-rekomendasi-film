import sys
import os

# Add app directory to path
app_path = os.path.join(os.path.dirname(__file__), 'app')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

print("=== DEBUGGING SERVER IMPORT ===")
print(f"Python path: {sys.path[:3]}")

try:
    print("1. Testing movie_service import...")
    from movie_service import MovieService
    print("   ✅ MovieService imported successfully")
    
    print("2. Testing global instance...")
    from movie_service import movie_service
    print(f"   ✅ movie_service instance: {type(movie_service)}")
    
    print("3. Testing load_movies...")
    movies = movie_service.load_movies()
    print(f"   ✅ Movies loaded: {len(movies)}")
    
    print("4. Testing get_genres...")
    genres = movie_service.get_genres(movies)
    print(f"   ✅ Genres found: {len(genres)}")
    
    print("5. Testing routes import...")
    from routes import main
    print("   ✅ Routes imported successfully")
    
    print("=== ALL IMPORTS SUCCESSFUL ===")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
