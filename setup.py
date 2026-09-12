import os
from pathlib import Path

def create_project_structure():
    # Dasar struktur folder
    base_dir = Path(__file__).parent
    dirs = [
        "app/static/images",
        "app/static/js",
        "app/static/css",
        "app/templates",
        "Data"
    ]
    
    # Buat direktori
    for dir_path in dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Buat file .env jika belum ada
    env_path = base_dir / '.env'
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write("# Konfigurasi Aplikasi\n")
            f.write("SECRET_KEY=dev-key-fallback\n")
            f.write("TMDB_API_KEY=ed6196ce9e32a462ca8ad5a7d43ae0e2\n")
            f.write("FLASK_ENV=development\n")
            f.write("FLASK_APP=run.py\n")
        print(f"Created file: {env_path}")
    
    print("\nStruktur folder berhasil dibuat!")

if __name__ == '__main__':
    create_project_structure()