#!/usr/bin/env python3
"""
Flask server runner with port 5003
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=== FLASK SERVER PORT 5003 ===")
    
    try:
        print("1. Importing app...")
        from app import create_app
        print("   [OK] App imported")
        
        print("2. Creating app...")
        app = create_app()
        print("   [OK] App created")
        
        print("3. Testing app context...")
        with app.app_context():
            from app.movie_service import movie_service
            movies = movie_service.load_movies()
            print(f"   [OK] Movies loaded: {len(movies)}")
            
            genres = movie_service.get_genres(movies)
            print(f"   [OK] Genres found: {len(genres)}")
        
        print("4. Starting server on port 5003...")
        print("   Server: http://127.0.0.1:5003")
        print("   Health: http://127.0.0.1:5003/health")
        print("   API: http://127.0.0.1:5003/api/genres")
        print("   Press CTRL+C to stop")
        print("-" * 50)
        
        # Run server on port 5003
        app.run(host='127.0.0.1', port=5003, debug=False, threaded=True)
        
    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()
