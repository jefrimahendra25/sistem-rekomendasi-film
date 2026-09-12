import re

def fix_popular_movies():
    # Baca isi file
    with open('app/routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cari posisi fungsi get_popular_movies
    start_idx = content.find('@bp.route(\'/api/movies/popular\')')
    if start_idx == -1:
        print("Tidak menemukan route /api/movies/popular")
        return False
    
    # Temukan awal dan akhir fungsi
    brace_count = 0
    func_start = content.rfind('def get_popular_movies', 0, start_idx)
    if func_start == -1:
        print("Tidak menemukan fungsi get_popular_movies")
        return False
    
    # Temukan awal dan akhir fungsi
    func_content = []
    in_function = False
    brace_count = 0
    start_line = 0
    
    lines = content.splitlines(True)
    for i, line in enumerate(lines):
        if 'def get_popular_movies' in line:
            in_function = True
            start_line = i
            func_content = []
            brace_count = 0
        
        if in_function:
            func_content.append(line)
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and len(func_content) > 1:
                # Ini adalah akhir fungsi
                break
    
    # Buat fungsi baru
    new_function = """@bp.route('/api/movies/popular')
@handle_errors
def get_popular_movies():
    \"\"\"Mendapatkan daftar film populer berdasarkan rating dengan dukungan filter\"\"\"
    global movie_features
    
    logger.info("\\n" + "="*50)
    logger.info("MEMPROSES PERMINTAAN FILM POPULER")
    logger.info("="*50)
    
    try:
        # Dapatkan parameter filter dari request
        genre_filter = request.args.get('with_genres', '').strip()
        year_filter = request.args.get('year', '').strip()
        
        logger.info(f"Filter yang diterima - Genre: {genre_filter}, Tahun: {year_filter}")
        
        # Load data jika belum dimuat
        if not is_dataframe_valid(movie_features):
            logger.warning("Data film belum dimuat, mencoba memuat...")
            movie_features = load_data()
            
            if not is_dataframe_valid(movie_features):
                logger.error("Gagal memuat data film")
                return jsonify({"error": "Gagal memuat data film"}), 500
        
        # Buat salinan DataFrame
        df = movie_features.copy()
        
        # Pastikan kolom yang diperlukan ada
        required_columns = ['title', 'vote_average', 'vote_count', 'overview', 'poster_path', 'release_date', 'genres']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Kolom yang hilang: {missing_columns}")
            return jsonify({"error": f"Format data tidak valid - kolom tidak ditemukan: {', '.join(missing_columns)}"}), 500
        
        # Filter film dengan vote_count minimal 10
        df = df[df['vote_count'] >= 10]
        
        # Terapkan filter genre jika ada
        if genre_filter:
            genre_filter = genre_filter.lower()
            logger.info(f"Menerapkan filter genre: {genre_filter}")
            
            # Pastikan kolom genres ada dan bukan NaN
            df = df[df['genres'].notna()]
            
            # Filter berdasarkan genre (case-insensitive)
            df = df[df['genres'].astype(str).str.lower().str.contains(genre_filter, na=False)]
            logger.info(f"Jumlah film setelah filter genre: {len(df)}")
        
        # Terapkan filter tahun jika ada
        if year_filter:
            try:
                year = int(year_filter)
                logger.info(f"Menerapkan filter tahun: {year}")
                
                # Ekstrak tahun dari release_date
                df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
                
                # Filter berdasarkan tahun
                df = df[df['year'] == year]
                logger.info(f"Jumlah film setelah filter tahun: {len(df)}")
                
                # Hapus kolom year sementara
                df = df.drop(columns=['year'])
            except (ValueError, TypeError) as e:
                logger.warning(f"Format tahun tidak valid: {year_filter}")
        
        if len(df) == 0:
            logger.warning("Tidak ada film yang sesuai dengan kriteria filter")
            return jsonify({
                "error": "Tidak ada film yang sesuai dengan kriteria filter",
                "filters": {"genre": genre_filter, "year": year_filter}
            }), 404
        
        # Hitung skor popularitas (rating * log(jumlah vote))
        df['popularity_score'] = df['vote_average'] * np.log1p(df['vote_count'])
        
        # Urutkan berdasarkan skor popularitas
        df = df.sort_values('popularity_score', ascending=False)
        
        # Ambil 20 film teratas
        popular_movies = df.head(20)
        
        # Format hasil
        result = []
        for _, movie in popular_movies.iterrows():
            poster_path = str(movie.get('poster_path', '')).strip()
            
            # Format path poster
            if poster_path and not poster_path.startswith(('http://', 'https://', '/static/')):
                poster_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
            
            # Dapatkan tahun rilis
            release_date = movie.get('release_date', '')
            release_year = movie.get('release_year', '')
            if pd.isna(release_year) and pd.notna(release_date):
                try:
                    release_year = pd.to_datetime(release_date).year
                except:
                    release_year = ''
            
            # Format genre
            genres = movie.get('genres', '')
            if pd.isna(genres):
                genres = ''
            
            result.append({
                'id': str(movie.get('id', '')),
                'title': str(movie.get('title', 'Judul tidak tersedia')).strip(),
                'overview': str(movie.get('overview', 'Deskripsi tidak tersedia')),
                'poster_path': poster_path if poster_path else '/static/images/no-poster.svg',
                'vote_average': float(movie.get('vote_average', 0)),
                'vote_count': int(movie.get('vote_count', 0)),
                'release_date': str(release_date) if pd.notna(release_date) else '',
                'release_year': int(release_year) if pd.notna(release_year) and str(release_year).isdigit() else 0,
                'genres': genres
            })
        
        logger.info(f"Mengembalikan {len(result)} film populer")
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error in get_popular_movies: {str(e)}\\n{traceback.format_exc()}"
        logger.error(error_msg)
        return jsonify({
            "error": "Terjadi kesalahan saat memuat film populer",
            "details": str(e)
        }), 500
"""
    
    # Ganti fungsi yang lama dengan yang baru
    new_content = content.replace("".join(func_content), new_function)
    
    # Tulis kembali file
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Fungsi get_popular_movies berhasil diperbarui")
    return True

if __name__ == "__main__":
    fix_popular_movies()
