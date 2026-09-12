from app.movie_service import movie_service
from difflib import SequenceMatcher
import math


def get_genres(movie):
    """Mengambil genre film menjadi set"""
    genres = set()

    for genre in movie.get('genres', []):
        if isinstance(genre, dict):
            genres.add(
                genre.get('name', '').lower().strip()
            )
        else:
            genres.add(
                str(genre).lower().strip()
            )

    return genres


def similarity(text1, text2):
    """Menghitung kemiripan teks"""

    return SequenceMatcher(
        None,
        str(text1).lower(),
        str(text2).lower()
    ).ratio()


def is_relevant(query_movie, movie):
    """
    Menentukan relevansi film
    berdasarkan genre, judul, dan sinopsis
    """

    query_genres = get_genres(query_movie)
    movie_genres = get_genres(movie)

    common_genres = query_genres.intersection(
        movie_genres
    )

    genre_match = len(common_genres) > 0

    title_similarity = similarity(
        query_movie.get('title', ''),
        movie.get('title', '')
    )

    overview_similarity = similarity(
        query_movie.get('overview', '')[:500],
        movie.get('overview', '')[:500]
    )

    query_words = set(
        query_movie.get('title', '').lower().split()
    )

    movie_words = set(
        movie.get('title', '').lower().split()
    )

    keyword_match = (
        len(
            query_words.intersection(movie_words)
        ) > 0
    )

    if genre_match:
        return True

    if title_similarity >= 0.5:
        return True

    if keyword_match:
        return True

    if overview_similarity >= 0.3:
        return True

    return False


# ==================================================
# NDCG
# ==================================================

def calculate_ndcg(relevance_scores):

    dcg = 0

    for i, rel in enumerate(relevance_scores):
        dcg += rel / math.log2(i + 2)

    ideal_scores = sorted(
        relevance_scores,
        reverse=True
    )

    idcg = 0

    for i, rel in enumerate(ideal_scores):
        idcg += rel / math.log2(i + 2)

    if idcg == 0:
        return 0

    return dcg / idcg


# ==================================================
# PRECISION@K
# ==================================================

def precision_at_k(relevance_scores, k):

    scores = relevance_scores[:k]

    if len(scores) == 0:
        return 0

    return sum(scores) / len(scores)


# ==================================================
# NDCG@K
# ==================================================

def ndcg_at_k(relevance_scores, k):

    scores = relevance_scores[:k]

    return calculate_ndcg(scores)


# ==================================================
# PROGRAM UTAMA
# ==================================================

if __name__ == "__main__":

    movie_title = input(
        "Masukkan judul film: "
    )

    print("\nMemuat dataset...")

    movies = movie_service.load_movies()

    if not movies:
        print("Dataset gagal dimuat.")
        exit()

    # ===== Split data (holdout) =====
    # Gunakan train sebagai pool untuk pencarian, dan test untuk query/evaluasi
    from random import Random

    rnd = Random(42)
    movies_shuffled = movies[:]
    rnd.shuffle(movies_shuffled)

    split_ratio = 0.8
    split_idx = int(len(movies_shuffled) * split_ratio)
    train_movies = movies_shuffled[:split_idx]
    test_movies = movies_shuffled[split_idx:]

    # Jalankan pencarian menggunakan pool train agar evaluasi out-of-sample
    search_results = movie_service.search_movies(
        movie_title,
        train_movies
    )

    if not search_results:
        print("Film tidak ditemukan.")
        exit()

    # Ambil maksimal 20 film
    search_results = search_results[:20]

    # Pastikan query movie berasal dari test jika memungkinkan
    query_movie = None
    query_lower = str(movie_title).lower().strip()
    for m in test_movies:
        if str(m.get('title','')).lower().strip() == query_lower:
            query_movie = m
            break

    # Jika tidak ada exact match judul di test, fallback ke dokumen teratas hasil pencarian
    # (tapi relevansi tetap dihitung pakai is_relevant, sehingga tetap ada evaluasi)
    if query_movie is None:
        query_movie = search_results[0]

    relevant_count = 0
    not_relevant_count = 0

    relevance_scores = []

    print("\n===== HASIL PENCARIAN =====")

    for rank, movie in enumerate(
        search_results,
        start=1
    ):

        relevant = is_relevant(
            query_movie,
            movie
        )

        score = 1 if relevant else 0

        relevance_scores.append(score)

        if relevant:
            relevant_count += 1
        else:
            not_relevant_count += 1

        status = (
            "Relevan"
            if relevant
            else "Tidak Relevan"
        )

        genres = []

        for g in movie.get('genres', []):

            if isinstance(g, dict):
                genres.append(
                    g.get('name', '')
                )
            else:
                genres.append(
                    str(g)
                )

        print(
            f"{rank}. "
            f"{movie.get('title')} | "
            f"{', '.join(genres)} | "
            f"{status}"
        )

    # =====================================
    # PRECISION
    # =====================================

    p5 = precision_at_k(
        relevance_scores,
        5
    )

    p10 = precision_at_k(
        relevance_scores,
        10
    )

    p20 = precision_at_k(
        relevance_scores,
        20
    )

    # =====================================
    # NDCG
    # =====================================

    ndcg5 = ndcg_at_k(
        relevance_scores,
        5
    )

    ndcg10 = ndcg_at_k(
        relevance_scores,
        10
    )

    ndcg20 = ndcg_at_k(
        relevance_scores,
        20
    )

    # =====================================
    # HASIL AKHIR
    # =====================================

    print("\n===================================")
    print(
        f"Film Acuan : "
        f"{query_movie.get('title')}"
    )

    print("\n----- PRECISION -----")
    print(f"P@5  = {p5:.3f}")
    print(f"P@10 = {p10:.3f}")
    print(f"P@20 = {p20:.3f}")

    print("\n----- NDCG -----")
    print(f"NDCG@5  = {ndcg5:.3f}")
    print(f"NDCG@10 = {ndcg10:.3f}")
    print(f"NDCG@20 = {ndcg20:.3f}")

    print("\n----- RINGKASAN -----")
    print(f"Total Hasil     : {len(search_results)}")
    print(f"Relevan         : {relevant_count}")
    print(f"Tidak Relevan   : {not_relevant_count}")

    print("===================================")