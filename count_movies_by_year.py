import pandas as pd
import os
import ast

def count_movies_by_year_and_analyze(csv_path):
    """
    Menganalisis jumlah film per tahun, genre, dan sutradara dari file CSV.
    
    Args:
        csv_path (str): Path ke file CSV yang berisi data film
        
    Returns:
        tuple: (result_year, result_genre, result_director, filtered_df)
    """
    try:
        # Baca file CSV
        df = pd.read_csv(csv_path, encoding='latin1')
        
        # Pastikan kolom yang dibutuhkan ada
        required_columns = ['year', 'genres', 'director']
        for col in required_columns:
            if col not in df.columns:
                return f"Kolom '{col}' tidak ditemukan dalam file CSV."
        
        # Konversi tipe data
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df = df.dropna(subset=['year'])
        df['year'] = df['year'].astype(int)
        
        # Hapus film dari tahun 1951-1992 dan tahun 2026
        df = df[~((df['year'] >= 1951) & (df['year'] <= 1992) | (df['year'] == 2026))]
        
        # 1. Analisis per tahun
        movies_per_year = df['year'].value_counts().sort_index()
        result_year = pd.DataFrame({
            'Tahun': movies_per_year.index,
            'Jumlah Film': movies_per_year.values
        }).sort_values('Tahun')
        
        # 2. Analisis per genre
        # Konversi string genre ke list
        try:
            df['genres'] = df['genres'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        except:
            # Jika gagal parsing, anggap sebagai string biasa
            df['genres'] = df['genres'].apply(lambda x: [x] if pd.notna(x) else [])
        
        # Hitung jumlah film per genre
        genre_counts = {}
        for genres in df['genres'].dropna():
            if isinstance(genres, list):
                for genre in genres:
                    genre = str(genre).strip()
                    if genre:
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        result_genre = pd.DataFrame({
            'Genre': list(genre_counts.keys()),
            'Jumlah Film': list(genre_counts.values())
        }).sort_values('Jumlah Film', ascending=False)
        
        # 3. Analisis per sutradara
        # Bersihkan data sutradara
        df['director'] = df['director'].fillna('Tidak Diketahui')
        director_counts = df['director'].value_counts()
        
        result_director = pd.DataFrame({
            'Sutradara': director_counts.index,
            'Jumlah Film': director_counts.values
        }).sort_values('Jumlah Film', ascending=False)
        
        return result_year, result_genre, result_director, df
        
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}"

def save_analysis(results, output_dir='Data'):
    """Menyimpan hasil analisis ke file Excel"""
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, 'analisis_film.xlsx')
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            results[0].to_excel(writer, sheet_name='Per Tahun', index=False)
            results[1].to_excel(writer, sheet_name='Per Genre', index=False)
            results[2].to_excel(writer, sheet_name='Per Sutradara', index=False)
        
        print(f"\nHasil analisis berhasil disimpan ke: {output_path}")
        return True
    except Exception as e:
        print(f"Gagal menyimpan file: {str(e)}")
        return False

def save_filtered_data(df, output_path):
    """
    Menyimpan data yang sudah difilter ke file CSV baru.
    
    Args:
        df (DataFrame): DataFrame yang sudah difilter
        output_path (str): Path untuk menyimpan file CSV baru
    """
    try:
        df.to_csv(output_path, index=False, encoding='latin1')
        print(f"\nData berhasil disimpan ke: {output_path}")
        return True
    except Exception as e:
        print(f"Gagal menyimpan file: {str(e)}")
        return False

if __name__ == "__main__":
    # Path ke file CSV
    input_csv = os.path.join('Data', 'film_indonesia_terbaru.csv')
    output_csv = os.path.join('Data', 'film_indonesia_terfilter.csv')
    
    # Periksa apakah file input ada
    if not os.path.exists(input_csv):
        print(f"File tidak ditemukan: {input_csv}")
    else:
        # Lakukan analisis
        results = count_movies_by_year_and_analyze(input_csv)
        
        if isinstance(results, tuple) and len(results) == 4:
            result_year, result_genre, result_director, filtered_df = results
            
            # Tampilkan ringkasan
            print("\n=== RINGKASAN ANALISIS ===")
            print(f"Total film: {len(filtered_df)}")
            print(f"\nJumlah film per tahun (5 tahun teratas):")
            print(result_year.head().to_string(index=False))
            
            print("\nJumlah film per genre (10 teratas):")
            print(result_genre.head(10).to_string(index=False))
            
            print("\nJumlah film per sutradara (10 teratas):")
            print(result_director.head(10).to_string(index=False))
            
            # Tanyakan apakah ingin menyimpan hasil analisis
            save_analysis_choice = input("\nApakah Anda ingin menyimpan hasil analisis lengkap? (y/n): ").strip().lower()
            if save_analysis_choice == 'y':
                save_analysis((result_year, result_genre, result_director))
            
            # Tanyakan apakah ingin menyimpan data yang sudah difilter
            save_filtered_choice = input("\nApakah Anda ingin menyimpan data yang sudah difilter? (y/n): ").strip().lower()
            if save_filtered_choice == 'y':
                save_filtered_data(filtered_df, output_csv)
        else:
            print(results)  # Tampilkan pesan error jika ada
