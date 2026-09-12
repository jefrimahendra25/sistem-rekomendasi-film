import requests
import time

def check_server():
    print("=== CHECKING SERVER STATUS ===")
    
    # Check if server is running
    try:
        response = requests.get('http://127.0.0.1:5002/health', timeout=3)
        print(f"Health check: {response.status_code}")
    except:
        print("Server is not running or not responding")
        return False
    
    # Test genres endpoint
    try:
        print("Testing /api/genres...")
        response = requests.get('http://127.0.0.1:5002/api/genres', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Genres loaded: {len(data.get('genres', []))}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Test movies endpoint
    try:
        print("Testing /api/movies...")
        response = requests.get('http://127.0.0.1:5002/api/movies?type=trending&page=1', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Movies loaded: {len(data.get('movies', []))}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    check_server()
