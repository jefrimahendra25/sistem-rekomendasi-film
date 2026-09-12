from app.movie_service import movie_service


def get_genres(movie):
    """
    Mengambil genre film menjadi set
    """
    genres = set()

    for genre in movie.get('genres', []):
        if isinstance(genre, dict):
            genres.add(genre.get('name', '').lower().strip())
        else:
            genres.add(str(genre).lower().strip())

    return genres


def is_relevant(query_movie, recommended_movie):
    """
    Film dianggap relevan jika memiliki
    minimal 1 genre yang sama
    """

    query_genres = get_genres(query_movie)
    rec_genres = get_genres(recommended_movie)

    common_genres = query_genres.intersection(rec_genres)

    return len(common_genres) > 0


def calculate_precision(query_movie, recommendations):

    relevant_movies = []
    not_relevant_movies = []

    for movie in recommendations:

        if is_relevant(query_movie, movie):
            relevant_movies.append(movie)
        else:
            not_relevant_movies.append(movie)

    total = len(recommendations)

    relevant_count = len(relevant_movies)

    precision = (
        relevant_count / total
        if total > 0 else 0
    )

    return {
        "total": total,
        "relevant": relevant_count,
        "not_relevant": len(not_relevant_movies),
        "precision": precision,
        "relevant_movies": relevant_movies,
        "not_relevant_movies": not_relevant_movies
    }


# ==================================================
# PROGRAM UTAMA
# ==================================================

if __name__ == "__main__":

    title = input("Masukkan judul film: ")

    print("\nMemuat dataset...")

    movies = movie_service.load_movies()

    if not movies:
        print("Data film gagal dimuat.")
        exit()

    # ===== Split data (holdout) =====
    # Gunakan train untuk pool rekomendasi agar evaluasi tidak memakai data yang sama untuk ranking & uji
    # (Metode sederhana: random split dengan seed tetap)
    from random import Random

    rnd = Random(42)
    movies_shuffled = movies[:]
    rnd.shuffle(movies_shuffled)

    split_ratio = 0.8
    split_idx = int(len(movies_shuffled) * split_ratio)
    train_movies = movies_shuffled[:split_idx]
    test_movies = movies_shuffled[split_idx:]

    # Cari film acuan hanya dari test
    query_movie = None
    query_title = title.lower()

    for movie in test_movies:
        if movie.get("title", "").lower() == query_title:
            query_movie = movie
            break

    if query_movie is None:
        print("Film tidak ditemukan.")
        exit()

    print(f"\nFilm Acuan : {query_movie['title']}")

    # Gunakan jumlah rekomendasi yang sama
    # seperti sistem (default = 10)
    # Pool rekomendasi diambil dari train
    recommendations = movie_service.recommend_movies(
        query_movie["id"],
        train_movies
    )

    result = calculate_precision(
        query_movie,
        recommendations
    )

    print("\n" + "=" * 50)
    print("HASIL EVALUASI PRECISION")
    print("=" * 50)

    print(f"Total Rekomendasi : {result['total']}")
    print(f"Film Relevan      : {result['relevant']}")
    print(f"Tidak Relevan     : {result['not_relevant']}")
    print(f"Precision         : {result['precision']:.4f}")

    print("\n===== FILM RELEVAN =====")

    for i, movie in enumerate(
        result["relevant_movies"],
        start=1
    ):
        print(f"{i}. {movie.get('title')}")

    print("\n===== FILM TIDAK RELEVAN =====")

    if len(result["not_relevant_movies"]) == 0:
        print("Tidak ada")
    else:
        for i, movie in enumerate(
            result["not_relevant_movies"],
            start=1
        ):
            print(f"{i}. {movie.get('title')}")