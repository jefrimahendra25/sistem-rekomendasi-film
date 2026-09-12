#!/usr/bin/env python3
"""
Check what the web API actually returns for popular tab
"""
import requests

def check_popular_api():
    """Check the popular tab API"""
    base_url = "http://127.0.0.1:5002"
    
    print("=== CHECKING WEB API RESULTS ===")
    
    # Check popular movies
    try:
        print("\n1. Testing /api/movies?type=popular...")
        response = requests.get(f"{base_url}/api/movies?type=popular&page=1", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            movies = data.get('movies', [])
            print(f"   ✅ Found {len(movies)} movies in popular tab")
            
            print("\n   Top 10 movies from popular tab:")
            print(f"   {'Rank':<6} {'Title':<45} {'Vote Avg':<10} {'Vote Count':<12}")
            print("   " + "-" * 80)
            for i, movie in enumerate(movies[:10], 1):
                title = movie.get('title', 'Unknown')[:45]
                vote_avg = movie.get('vote_average', 0)
                vote_count = movie.get('vote_count', 0)
                print(f"   {i:<6} {title:<45} {vote_avg:<10.2f} {vote_count:<12}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    # Check search for "ada apa dengan cinta"
    try:
        print("\n2. Testing /api/search?q=ada apa dengan cinta...")
        response = requests.get(f"{base_url}/api/search?q=ada apa dengan cinta", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            movies = data.get('movies', [])
            print(f"   ✅ Found {len(movies)} movies from search")
            
            print("\n   Top 10 movies from search:")
            print(f"   {'Rank':<6} {'Title':<45} {'Vote Avg':<10} {'Vote Count':<12}")
            print("   " + "-" * 80)
            for i, movie in enumerate(movies[:10], 1):
                title = movie.get('title', 'Unknown')[:45]
                vote_avg = movie.get('vote_average', 0)
                vote_count = movie.get('vote_count', 0)
                print(f"   {i:<6} {title:<45} {vote_avg:<10.2f} {vote_count:<12}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

if __name__ == '__main__':
    check_popular_api()
