import requests

def test_genres_api():
    try:
        response = requests.get('http://127.0.0.1:5002/api/genres', timeout=5)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Genres found: {len(data.get("genres", []))}')
            print('Sample genres:')
            for i, genre in enumerate(data.get('genres', [])[:3]):
                print(f'  {i+1}. {genre}')
        else:
            print(f'Error: {response.text}')
    except Exception as e:
        print(f'Connection error: {e}')

if __name__ == "__main__":
    test_genres_api()
