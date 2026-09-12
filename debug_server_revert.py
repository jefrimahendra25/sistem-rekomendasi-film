import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=== DEBUGGING SERVER REVERT ISSUE ===")

def test_import_sequence():
    """Test the exact import sequence that run.py uses"""
    try:
        print("1. Testing app import sequence...")
        
        # Test step by step like run.py
        print("   1a. Importing app.create_app...")
        from app import create_app
        print("       ✅ create_app imported")
        
        print("   1b. Creating app...")
        app = create_app()
        print("       ✅ App created")
        
        print("   1c. Testing app context...")
        with app.app_context():
            print("       ✅ App context works")
            
            print("   1d. Testing movie_service import...")
            from app.movie_service import movie_service
            print("       ✅ movie_service imported")
            
            print("   1e. Testing movie_service functionality...")
            movies = movie_service.load_movies()
            print(f"       ✅ Movies loaded: {len(movies)}")
            
            genres = movie_service.get_genres(movies)
            print(f"       ✅ Genres found: {len(genres)}")
        
        print("=== FULL APP WORKS PERFECTLY ===")
        return True
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_fallback():
    """Test simple fallback"""
    try:
        print("2. Testing simple fallback...")
        from run_simple import create_simple_app as create_app
        print("   ✅ Simple app imported")
        
        app = create_app()
        print("   ✅ Simple app created")
        
        return True
    except Exception as e:
        print(f"❌ Simple app error: {e}")
        return False

# Run tests
full_app_works = test_import_sequence()
simple_app_works = test_simple_fallback()

print(f"\n=== SUMMARY ===")
print(f"Full app works: {full_app_works}")
print(f"Simple app works: {simple_app_works}")

if full_app_works:
    print("✅ Server should use full app")
else:
    print("❌ Server will fallback to simple app")
