import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=== TESTING FULL APP IMPORT ===")

try:
    print("1. Testing create_app import...")
    from app import create_app
    print("   ✅ create_app imported successfully")
    
    print("2. Testing app creation...")
    app = create_app()
    print("   ✅ App created successfully")
    
    print("3. Testing app context...")
    with app.app_context():
        print("   ✅ App context works")
        
        print("4. Testing movie_service in app context...")
        from app.movie_service import movie_service
        movies = movie_service.load_movies()
        print(f"   ✅ Movies loaded: {len(movies)}")
        
        genres = movie_service.get_genres(movies)
        print(f"   ✅ Genres found: {len(genres)}")
    
    print("=== FULL APP WORKS PERFECTLY ===")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
