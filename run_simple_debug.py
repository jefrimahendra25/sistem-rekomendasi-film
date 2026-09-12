#!/usr/bin/env python3
"""
Simple debug runner for Flask app
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=== SIMPLE DEBUG RUNNER ===")
    
    try:
        # Test imports first
        print("1. Testing imports...")
        from app import create_app
        print("   ✅ create_app imported")
        
        # Create app
        print("2. Creating app...")
        app = create_app()
        print("   ✅ App created")
        
        # Test routes
        print("3. Testing routes...")
        with app.app_context():
            from app.movie_service import movie_service
            movies = movie_service.load_movies()
            print(f"   ✅ Movies loaded: {len(movies)}")
            
            genres = movie_service.get_genres(movies)
            print(f"   ✅ Genres found: {len(genres)}")
        
        # Run app
        print("4. Starting server...")
        app.run(host='127.0.0.1', port=5002, debug=False)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
