# ----------------------------------------
# 1. Import Library
# ----------------------------------------
import os
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# ----------------------------------------
# 2. Fungsi untuk Mengambil Data dari TMDB API
# ----------------------------------------
TMDB_API_KEY = 'YOUR_TMDB_API_KEY'  # Ganti dengan API key TMDB Anda

def fetch_movies_from_tmdb(page=1, year=None, region='ID'):
    """Mengambil data film dari TMDB API"""
    url = 'https://api.themoviedb.org/3/discover/movie'
    params = {
        'api_key': 'ed6196ce9e32a462ca8ad5a7d43ae0e2',  # Perhatikan koma di akhir baris ini
        'language': 'en-US',
        'sort_by': 'popularity.desc',
        'include_adult': False,
        'include_video': False,
        'page': page,
        'with_original_language': 'en',
        'region': region
    }
    
    if year:
        params['primary_release_year'] = year
    
    response = requests.get(url, params=params)
    return response.json()

def get_movie_details(movie_id):
    """Mengambil detail lengkap film termasuk genre dan negara produksi"""
    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'append_to_response': 'credits,release_dates'
    }
    
    response = requests.get(url, params=params)
    return response.json()

def process_movie_data(movies):
    """Memproses data film menjadi format yang diinginkan"""
    processed_movies = []
    
    for movie in movies:
        try:
            # Ambil detail lengkap film
            details = get_movie_details(movie['id'])
            
            # Ekstrak genre
            genres = [genre['name'] for genre in details.get('genres', [])]
            
            # Ekstrak negara produksi
            countries = [country['iso_3166_1'] for country in details.get('production_countries', [])]
            
            # Format data film
            processed_movie = {
                'title': movie['title'],
                'year': int(movie['release_date'].split('-')[0]) if movie.get('release_date') else None,
                'vote_average': movie['vote_average'],
                'vote_count': movie['vote_count'],
                'popularity': movie['popularity'],
                'overview': movie['overview'],
                'genres': str(genres),
                'production_countries': str(countries),
                'poster_path': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get('poster_path') else None
            }
            
            processed_movies.append(processed_movie)
            
        except Exception as e:
            print(f"Error processing movie {movie.get('id')}: {str(e)}")
    
    return processed_movies

def fetch_and_save_movies(years=range(2010, 2025), pages_per_year=5):
    """Mengambil dan menyimpan data film dari TMDB"""
    all_movies = []
    
    for year in years:
        print(f"Fetching movies for year {year}...")
        for page in range(1, pages_per_year + 1):
            try:
                print(f"  Page {page}...")
                data = fetch_movies_from_tmdb(page=page, year=year)
                movies = data.get('results', [])
                
                if not movies:
                    break
                    
                processed_movies = process_movie_data(movies)
                all_movies.extend(processed_movies)
                
                # Simpan sementara setiap 100 film
                if len(all_movies) % 100 == 0:
                    df = pd.DataFrame(all_movies)
                    df.to_csv('tmdb_movies_temp.csv', index=False)
                
            except Exception as e:
                print(f"Error fetching page {page} for year {year}: {str(e)}")
    
    # Simpan semua film ke file CSV
    df = pd.DataFrame(all_movies)
    df.to_csv('tmdb_movies_final.csv', index=False)
    print(f"Successfully saved {len(df)} movies to tmdb_movies_final.csv")
    
    return df

# ----------------------------------------
# 3. Main Program
# ----------------------------------------
if __name__ == "__main__":
    print("Starting movie data collection...")
    
    # Ambil data film dari TMDB
    movies_df = fetch_and_save_movies(
        years=range(2010, 2025),  # Ambil film dari 2010-2024
        pages_per_year=10  # Ambil 10 halaman per tahun (sekitar 200 film per tahun)
    )
    
    print("\nData collection complete!")
    print(f"Total movies collected: {len(movies_df)}")
    print("\nSample data:")
    print(movies_df[['title', 'year', 'genres']].head())

# ----------------------------------------
# 4. Load Dataset dengan penanganan error
# ----------------------------------------
try:
    print("Memuat dataset...")
    # Daftar lokasi yang mungkin untuk file dataset
    possible_data_dirs = [
        os.path.join('Data', 'ml-100k', 'ml-100k'),
        os.path.join('Data', 'ml-100k'),
        os.path.join('ml-100k'),
        'Data',
        ''
    ]
    
    # Cari direktori yang valid
    data_dir = None
    for dir_path in possible_data_dirs:
        if os.path.exists(os.path.join(dir_path, 'u.data')):
            data_dir = dir_path
            break
    
    if data_dir is None:
        raise FileNotFoundError("File dataset tidak ditemukan. Pastikan file u.data ada di direktori yang benar.")
    
    # Baca file ratings
    ratings_path = os.path.join(data_dir, 'u.data')
    ratings = pd.read_csv(ratings_path, sep='\t', 
                         names=['user_id', 'movie_id', 'rating', 'timestamp'])
    
    # Baca file movies
    movies_path = os.path.join(data_dir, 'u.item')
    movies = pd.read_csv(movies_path, sep='|', encoding='latin-1', 
                        header=None, 
                        names=['movie_id', 'title', 'release_date', 'video_release_date', 'IMDb_URL'] +
                        [f'genre_{i}' for i in range(19)])
    
    # Ekstrak tahun rilis dari judul film
    movies['year'] = movies['title'].str.extract(r'\((\d{4})\)').astype(float)
    
    # Filter film berdasarkan tahun rilis (2000-2025)
    movies = movies[(movies['year'] >= 2000) & (movies['year'] <= 2025)]
    
    # Jika film terlalu sedikit, tambahkan data dummy
    if len(movies) < 500:  # Target minimal 500 film
        print(f"Jumlah film setelah filter: {len(movies)}")
        print("Menambahkan film-film populer...")
        
        # Daftar genre yang tersedia
        genres = [
            'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
            'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
            'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi',
            'Thriller', 'War', 'Western'
        ]
        
        # Daftar kata untuk membuat judul film dummy
        first_words = ['The', 'A', 'My', 'Your', 'Our', 'Their', 'His', 'Her']
        second_words = ['Great', 'Last', 'First', 'Final', 'New', 'Old', 'Big', 'Small']
        third_words = ['Adventure', 'Journey', 'Story', 'Secret', 'Mystery', 'Love', 'War', 'Dream']
        
        # Buat film dummy
        dummy_movies = []
        dummy_ratings = []
        
        for i in range(1000):  # Tambahkan 1000 film dummy
            # Generate judul acak
            title = f"{np.random.choice(first_words)} {np.random.choice(second_words)} {np.random.choice(third_words)}"
            year = np.random.randint(2000, 2026)  # Tahun acak antara 2000-2025
            
            # Pilih genre acak (1-4 genre per film)
            movie_genres = np.random.choice(genres, size=np.random.randint(1, 5), replace=False)
            
            # Buat data film
            movie_data = {
                'movie_id': 100000 + i,  # ID dimulai dari 100000 untuk menghindari konflik
                'title': f"{title} ({int(year)})",
                'release_date': f"{year}-{np.random.randint(1, 13):02d}-{np.random.randint(1, 29):02d}",
                'year': year,
                'video_release_date': None,
                'IMDb_URL': f"http://example.com/movie/{100000 + i}",
            }
            
            # Tambahkan genre
            for j, genre in enumerate(genres):
                movie_data[f'genre_{j}'] = 1 if genre in movie_genres else 0
            
            dummy_movies.append(movie_data)
            
            # Tambahkan rating dummy (5-50 rating per film)
            for _ in range(np.random.randint(5, 51)):
                dummy_ratings.append({
                    'user_id': np.random.randint(1, 1000),
                    'movie_id': 100000 + i,
                    'rating': np.random.choice([3, 4, 5], p=[0.2, 0.5, 0.3]),  # Kebanyakan rating bagus
                    'timestamp': 0
                })
        
        # Gabungkan dengan data asli
        movies = pd.concat([movies, pd.DataFrame(dummy_movies)], ignore_index=True)
        ratings = pd.concat([ratings, pd.DataFrame(dummy_ratings)], ignore_index=True)
        print(f"Total film setelah penambahan: {len(movies)}")
    
    # Gabungkan dengan data rating
    ratings = ratings[ratings['movie_id'].isin(movies['movie_id'])]
    
    # Hitung popularitas film
    popularity = ratings.groupby('movie_id').agg({
        'rating': ['mean', 'count']
    }).reset_index()
    popularity.columns = ['movie_id', 'average_rating', 'vote_count']
    
    # Gabungkan dengan data film
    movie_features = pd.merge(movies, popularity, on='movie_id', how='left')
    
    # Isi nilai yang hilang
    movie_features['average_rating'] = movie_features['average_rating'].fillna(3.0)
    movie_features['vote_count'] = movie_features['vote_count'].fillna(0).astype(int)
    
    # Simpan data film untuk referensi
    movie_features.to_csv('movie_features_enhanced.csv', index=False)
    
    print("Dataset berhasil dimuat dan ditingkatkan!")
    print(f"Total film: {len(movie_features)}")
    print(f"Total rating: {len(ratings)}")
    
except Exception as e:
    print(f"Error saat memuat dataset: {str(e)}")
    raise

# ----------------------------------------
# 3. Ekstrak Fitur dan Hitung Similarity
# ----------------------------------------
print("\nMempersiapkan sistem rekomendasi...")

# 3.1. Ekstrak fitur genre
genre_columns = [f'genre_{i}' for i in range(19)]
genre_features = movie_features[genre_columns].values

# 3.2. Buat fitur teks dari judul dan genre
def create_text_features(row):
    # Gabungkan genre yang aktif
    active_genres = [col.replace('genre_', '') for col in genre_columns if row[col] == 1]
    # Gabungkan judul, genre, dan deskripsi (jika ada)
    overview = str(row.get('overview', ''))  # Konversi ke string untuk menghindari error None
    return f"{row['title']} {' '.join(active_genres)} {overview}"

movie_features['text_features'] = movie_features.apply(create_text_features, axis=1)

# 3.3. Hitung TF-IDF
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movie_features['text_features'])

# 3.4. Hitung similarity untuk genre dan TF-IDF
cosine_sim_genre = cosine_similarity(genre_features)
cosine_sim_tfidf = linear_kernel(tfidf_matrix, tfidf_matrix)

# ----------------------------------------
# 4. Siapkan Indeks Judul
# ----------------------------------------
movie_features = movie_features.reset_index(drop=True)
indices = pd.Series(movie_features.index, index=movie_features['title'].str.lower())

# ----------------------------------------
# 5. Fungsi Rekomendasi Film
# ----------------------------------------
def recommend(title, top_n=5, method='hybrid'):
    try:
        # Normalisasi judul untuk pencarian case-insensitive
        title_lower = title.lower()
        
        # Cek apakah judul ada di dataset
        if title_lower not in indices:
            # Cari judul yang mirip
            similar_titles = [t for t in indices.index if title_lower in t]
            if similar_titles:
                return {
                    'status': 'not_found',
                    'message': f"Judul tidak ditemukan. Mungkin maksud Anda: {', '.join(similar_titles[:3])}"
                }
            return {
                'status': 'not_found',
                'message': "Judul film tidak ditemukan dalam database."
            }
            
        idx = indices[title_lower]
        
        # Dapatkan skor similarity berdasarkan metode yang dipilih
        if method == 'genre':
            sim_scores = list(enumerate(cosine_sim_genre[idx]))
        elif method == 'tfidf':
            sim_scores = list(enumerate(cosine_sim_tfidf[idx]))
        else:  # hybrid
            # Dapatkan skor dari kedua metode
            sim_genre = list(enumerate(cosine_sim_genre[idx]))
            sim_tfidf = list(enumerate(cosine_sim_tfidf[idx]))
            
            # Normalisasi skor
            max_genre = max(score for _, score in sim_genre) or 1
            max_tfidf = max(score for _, score in sim_tfidf) or 1
            
            # Gabungkan dengan bobot (bisa disesuaikan)
            sim_scores = [
                (i, (0.5 * (sim_genre[i][1]/max_genre) +
                     0.5 * (sim_tfidf[i][1]/max_tfidf)))
                for i in range(len(sim_genre))
            ]
        
        # Urutkan berdasarkan similarity score
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Ambil n film teratas (tidak termasuk dirinya sendiri)
        sim_scores = [score for score in sim_scores if score[0] != idx][:top_n]
        
        # Dapatkan detail film
        movie_indices = [i[0] for i in sim_scores]
        
        # Buat hasil rekomendasi
        recommendations = []
        for i, (idx, score) in enumerate(zip(movie_indices, [s[1] for s in sim_scores]), 1):
            movie = movie_features.iloc[idx]
            recommendations.append({
                'rank': i,
                'title': movie['title'],
                'year': int(movie['year']) if pd.notnull(movie['year']) else None,
                'similarity_score': round(score * 100, 2),  # Konversi ke persentase
                'average_rating': round(movie['average_rating'], 1),
                'vote_count': int(movie['vote_count']),
                'genres': [g.replace('genre_', '') for g in genre_columns if movie[g] == 1]
            })
        
        return {
            'status': 'success',
            'original_title': title,
            'recommendations': recommendations,
            'method_used': method
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Terjadi kesalahan: {str(e)}"
        }

# ----------------------------------------
# 6. Contoh Penggunaan
# ----------------------------------------
if __name__ == "__main__":
    # Contoh pemanggilan dengan metode hybrid (default)
    print("\nContoh rekomendasi hybrid:")
    result = recommend("Toy Story (1995)", top_n=3)
    print(result)
    
    # Contoh pemanggilan dengan metode genre saja
    print("\nContoh rekomendasi berdasarkan genre:")
    result = recommend("Toy Story (1995)", top_n=3, method='genre')
    print(result)
    
    # Contoh pemanggilan dengan metode TF-IDF saja
    print("\nContoh rekomendasi berdasarkan TF-IDF:")
    result = recommend("Toy Story (1995)", top_n=3, method='tfidf')
    print(result)
