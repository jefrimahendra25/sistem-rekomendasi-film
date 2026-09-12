import os
import pandas as pd
import requests
from datetime import datetime
import time

# Konfigurasi TMDB
TMDB_API_KEY = 'ed6196ce9e32a462ca8ad5a7d43ae0e2'

def fetch_indonesian_movies():
    """Mengambil film Indonesia dari TMDB API untuk tahun 2000-2025"""
    all_movies = []

    # Parameter untuk film Indonesia
    base_params = {
        'api_key': TMDB_API_KEY,
        'language': 'id-ID',
        'region': 'ID',
        'with_original_language': 'id',
        'sort_by': 'popularity.desc',
        'include_adult': False,
        'include_video': False,
    }

    print('Mengambil film Indonesia dari TMDB API (2000-2025)...')

    for year in range(2000, 2026):
        print(f'\nMengambil film tahun {year}...')
        params = base_params.copy()
        params['primary_release_year'] = year

        year_movies = []

        # Ambil maksimal 5 halaman per tahun (sekitar 100 film)
        for page in range(1, 6):
            params['page'] = page

            try:
                response = requests.get('https://api.themoviedb.org/3/discover/movie', params=params)
                data = response.json()

                if 'results' not in data or not data['results']:
                    print(f'  Tidak ada film lagi di halaman {page}')
                    break

                print(f'  Halaman {page}: {len(data["results"])} film ditemukan')

                for movie in data['results']:
                    # Ambil detail lengkap film
                    try:
                        detail_response = requests.get(
                            f'https://api.themoviedb.org/3/movie/{movie["id"]}',
                            params={'api_key': TMDB_API_KEY, 'language': 'id-ID'}
                        )
                        details = detail_response.json()

                        movie_data = {
                            'id': details.get('id'),
                            'title': details.get('title', ''),
                            'original_title': details.get('original_title', ''),
                            'overview': details.get('overview', ''),
                            'release_date': details.get('release_date', ''),
                            'year': year,
                            'popularity': details.get('popularity', 0),
                            'vote_average': details.get('vote_average', 0),
                            'vote_count': details.get('vote_count', 0),
                            'poster_path': f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}" if details.get('poster_path') else None,
                            'genres': [g['name'] for g in details.get('genres', [])],
                            'production_countries': [c['iso_3166_1'] for c in details.get('production_countries', [])],
                            'runtime': details.get('runtime'),
                            'original_language': details.get('original_language')
                        }

                        year_movies.append(movie_data)

                    except Exception as e:
                        print(f'    Error detail film {movie["id"]}: {e}')
                        continue

                # Jeda antar halaman
                time.sleep(0.5)

            except Exception as e:
                print(f'  Error halaman {page}: {e}')
                break

        all_movies.extend(year_movies)
        print(f'  Total film tahun {year}: {len(year_movies)}')

        # Simpan progress setiap tahun
        if year % 5 == 0 and all_movies:
            df_temp = pd.DataFrame(all_movies)
            df_temp.to_csv(f'Data/film_indonesia_progress_{year}.csv', index=False)
            print(f'  Progress tersimpan: {len(all_movies)} film')

    # Simpan hasil akhir
    df = pd.DataFrame(all_movies)
    df.to_csv('Data/film_indonesia_terfilter.csv', index=False, encoding='utf-8')

    print(f'\n=== SELESAI ===')
    print(f'Total film Indonesia (2000-2025): {len(df)}')
    print('Data tersimpan di: Data/film_indonesia_terfilter.csv')

    return df

if __name__ == '__main__':
    fetch_indonesian_movies()
