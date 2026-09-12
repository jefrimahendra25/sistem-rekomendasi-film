import requests
import json
import time

def test_endpoints():
    print("=== TESTING API ENDPOINTS ===")
    base_url = "http://127.0.0.1:5002"
    
    endpoints = [
        "/health",
        "/api/genres", 
        "/api/movies?type=trending&page=1",
        "/api/movies?type=newest&page=1",
        "/api/movies?type=popular&page=1",
        "/api/movies?type=trending&page=1&genre=28",
        "/api/welcome"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting {endpoint}...")
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'genres' in data:
                        print(f"  ✅ Genres: {len(data['genres'])}")
                    elif 'movies' in data:
                        print(f"  ✅ Movies: {len(data['movies'])}")
                    elif 'status' in data:
                        print(f"  ✅ Status: {data['status']}")
                    else:
                        print(f"  ✅ Response: {str(data)[:100]}...")
                except:
                    print(f"  ✅ Response: {response.text[:100]}...")
            else:
                print(f"  ❌ Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Connection error: {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_endpoints()
