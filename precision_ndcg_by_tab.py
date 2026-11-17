from app.movie_service import movie_service

import argparse
import math
import re
from typing import List, Dict, Optional


def get_genres(movie: Dict) -> set:
    """Mengambil genre film menjadi set lowercase."""
    genres = set()

    for genre in movie.get('genres', []):
        if isinstance(genre, dict):
            name = genre.get('name', '').lower().strip()
            if name:
                genres.add(name)
        else:
            val = str(genre).lower().strip()
            if val:
                genres.add(val)

    return genres


def similarity(text1, text2):
    """Menghitung kemiripan teks (identik dengan precision_search.py)."""
    from difflib import SequenceMatcher

    text1 = str(text1 or '').lower().strip()
    text2 = str(text2 or '').lower().strip()
    if not text1 or not text2:
        return 0.0

    return SequenceMatcher(
        None,
        text1,
        text2,
    ).ratio()


def is_relevant(query_movie: Dict, movie: Dict) -> bool:
    """Use the same title, synopsis, or combined genre/director evidence as the app."""
    return movie_service.get_relevance_status(
        query_movie,
        movie,
        semantic_similarity=movie.get('semantic_similarity'),
        synopsis_similarity=movie.get('synopsis_similarity'),
    )[0]


def relevance_grade(query_movie: Dict, movie: Dict) -> int:
    """Return binary relevance using FilmKu's title, synopsis, or genre/director rule."""
    return int(is_relevant(query_movie, movie))


def is_reference_movie(query_movie: Dict, movie: Dict) -> bool:
    query_id = query_movie.get('id')
    movie_id = movie.get('id')
    if query_id is not None and movie_id is not None:
        return str(query_id) == str(movie_id)

    query_title = normalize_title(query_movie.get('title', ''))
    movie_title = normalize_title(movie.get('title', ''))
    return bool(query_title) and query_title == movie_title


def precision_at_k(relevance_scores: List[int], k: int) -> Optional[float]:
    if k <= 0:
        return 0.0

    if len(relevance_scores) < k:
        return None

    return sum(int(bool(score)) for score in relevance_scores[:k]) / k


def calculate_ndcg(
    relevance_scores: List[int],
    ideal_relevance_scores: Optional[List[int]] = None,
) -> float:
    dcg = 0.0

    for i, rel in enumerate(relevance_scores):
        dcg += int(bool(rel)) / math.log2(i + 2)

    ideal_scores = sorted(
        ideal_relevance_scores if ideal_relevance_scores is not None else relevance_scores,
        key=bool,
        reverse=True,
    )[:len(relevance_scores)]

    idcg = 0.0
    for i, rel in enumerate(ideal_scores):
        idcg += int(bool(rel)) / math.log2(i + 2)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def ndcg_at_k(relevance_scores: List[int], k: int) -> Optional[float]:
    if k <= 0:
        return 0.0
    if len(relevance_scores) < k:
        return None
    return calculate_ndcg(relevance_scores[:k], relevance_scores)


def calculate_ranking_metrics(
    ranking: List[Dict],
    query_movie: Dict,
    k_list: List[int],
):
    """Calculate binary Precision and NDCG using title/synopsis relevance."""
    recommendations = [
        movie for movie in ranking
        if not is_reference_movie(query_movie, movie)
    ]
    relevance_scores = [
        relevance_grade(query_movie, movie)
        for movie in recommendations
    ]
    metrics = {}
    for k in k_list:
        metrics[f'P@{k}'] = precision_at_k(relevance_scores, k)
        metrics[f'NDCG@{k}'] = ndcg_at_k(relevance_scores, k)
        metrics[f'Relevant@{k}'] = sum(relevance_scores[:k])
    return metrics


def calculate_sortcons(ranking: List[Dict]) -> float:
    """Fraction of all pairs matching the PCC, popularity, and weighted-rating order."""
    if len(ranking) < 2:
        return 1.0

    def score(movie: Dict, key: str) -> float:
        value = movie_service._as_float(movie.get(key))
        return value if math.isfinite(value) else 0.0

    def order_key(movie: Dict):
        return (
            round(score(movie, 'pcc_similarity'), 2),
            score(movie, 'popularity'),
            movie_service._weighted_rating(movie),
        )

    total_pairs = len(ranking) * (len(ranking) - 1) / 2
    consistent_pairs = sum(
        order_key(ranking[first_index]) >= order_key(ranking[second_index])
        for first_index in range(len(ranking) - 1)
        for second_index in range(first_index + 1, len(ranking))
    )
    return consistent_pairs / total_pairs


def format_ranking_metrics(metrics: Dict, k_list: List[int]) -> str:
    """Format the shared Precision@K and NDCG@K values for diagram captions."""
    k_values = '/'.join(str(k) for k in k_list)
    precision_values = ' / '.join(
        f"{metrics[f'P@{k}']:.3f}" if metrics[f'P@{k}'] is not None else 'N/A'
        for k in k_list
    )
    ndcg_values = ' / '.join(
        f"{metrics[f'NDCG@{k}']:.3f}" if metrics[f'NDCG@{k}'] is not None else 'N/A'
        for k in k_list
    )
    return (
        f"Precision@{k_values}: {precision_values}\n"
        f"NDCG@{k_values}: {ndcg_values}"
    )


def normalize_title(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', str(title).lower()).strip()


def find_exact_reference_movie(query: str, movies: List[Dict]) -> Optional[Dict]:
    """Return a reference movie only when the query exactly matches one title."""
    exact_matches = find_reference_movies(query, movies)
    return exact_matches[0] if len(exact_matches) == 1 else None


def find_reference_movies(query: str, movies: List[Dict]) -> List[Dict]:
    """Return all movies whose normalized title exactly matches the query."""
    normalized_query = normalize_title(query)
    if not normalized_query:
        return []
    return [
        movie for movie in movies
        if normalize_title(movie.get('title', '')) == normalized_query
    ]


def get_content_ranking(
    query: str,
    movies: List[Dict],
    top_n: int = 20,
):
    """Return the same filled and ordered candidate list as the search endpoint."""
    candidates = movie_service.recommend_similar_movies(
        query=query,
        movies=movies,
        top_n=top_n,
    )
    search_mode = "Content-Based Filtering (TF-IDF + metadata)"
    if candidates is None:
        candidates = movie_service.search_movies(query, movies)
        search_mode = "TF-IDF content search fallback"
    candidates = movie_service.fill_search_results(
        query,
        movies,
        candidates,
        top_n=top_n,
    )
    if not candidates:
        return [], search_mode

    if any('semantic_similarity' in movie for movie in candidates):
        search_mode = (
            "Content-Based Filtering (TF-IDF + semantic synopsis similarity)"
        )

    pcc_scores = movie_service.calculate_pcc_scores(query, candidates)
    for movie in candidates:
        movie_id = movie.get('id')
        if movie_id is not None:
            movie['pcc_similarity'] = pcc_scores.get(str(movie_id), 0.0)
        if not movie.get('relevance'):
            movie['relevance'] = (
                'Belum ada kecocokan kuat pada judul, sinopsis, genre, '
                'atau sutradara'
            )

    ranked_candidates = movie_service.sort_search_results_by_pcc(candidates)
    return ranked_candidates[:top_n], search_mode


def normalize_queries(query_arguments: List[str], prompted_query: str = '') -> List[str]:
    """Accept multiple CLI or prompted queries, including pipe-separated values."""
    raw_queries = query_arguments if query_arguments else [prompted_query]
    return [
        query.strip()
        for value in raw_queries
        for query in value.split('|')
        if query.strip()
    ]


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description='Search film recommendations and optionally calculate Precision@K and NDCG@K.'
    )
    parser.add_argument(
        'queries',
        nargs='*',
        help='one or more free-form search queries; separate queries with "|" or separate arguments',
    )
    return parser


def evaluate_query(query: str, movies: List[Dict], k_list: List[int]):
    query_movie = find_exact_reference_movie(query, movies)
    web_ranking, search_mode = get_content_ranking(
        query,
        movies,
        top_n=20,
    )
    if not web_ranking:
        print(f"\nTidak ada hasil untuk query '{query}'.")
        return

    web_ranking = web_ranking[:20]

    print(f"\n=== Query pencarian: {query} ===")
    print(f"Mode pencarian: {search_mode}")
    print(f"Jumlah hasil: {len(web_ranking)}")
    print("\n=== HASIL PENCARIAN (urutan seperti web) ===")
    for rank, movie in enumerate(web_ranking, start=1):
        genres = [
            genre.get('name', '') if isinstance(genre, dict) else str(genre)
            for genre in movie.get('genres', [])
        ]
        print(
            f"{rank}. {movie.get('title')} | "
            f"{', '.join(genres)} | {movie.get('relevance', '')} | "
            f"PCC {movie.get('pcc_similarity', 0.0) * 100:.2f}%"
        )

    if query_movie is None:
        print(
            "\nPrecision@K dan NDCG@K tidak dihitung karena query pencarian "
            "bebas tidak menentukan satu film acuan secara persis."
        )
        return

    evaluation_ranking = [
        movie for movie in web_ranking
        if query_movie is None or not is_reference_movie(query_movie, movie)
    ]
    max_k = max(k_list, default=20)
    if len(evaluation_ranking) < max_k:
        expanded_ranking, _ = get_content_ranking(
            query,
            movies,
            top_n=max(20, max_k) + 1,
        )
        evaluation_ranking = [
            movie for movie in expanded_ranking
            if not is_reference_movie(query_movie, movie)
        ][:max_k]

    print(f"\nFilm acuan untuk evaluasi: {query_movie.get('title')}")
    print(
        "Metrik dihitung dari daftar evaluasi; film acuan dikeluarkan "
        "dan kandidat tambahan (jika diperlukan) tidak ditampilkan."
    )
    print(
        "Kriteria relevansi evaluasi: kecocokan judul, sinopsis, atau "
        "gabungan genre dan sutradara."
    )
    print("\n=== METRIK PADA URUTAN PENCARIAN PCC ===")
    metrics = calculate_ranking_metrics(evaluation_ranking, query_movie, k_list)
    for k in k_list:
        precision = metrics[f'P@{k}']
        ndcg = metrics[f'NDCG@{k}']
        precision_output = f"{precision:.3f}" if precision is not None else 'N/A'
        ndcg_output = f"{ndcg:.3f}" if ndcg is not None else 'N/A'
        print(f"  Film relevan@{k} = {metrics[f'Relevant@{k}']}/{k}")
        print(f"  Precision@{k} = {precision_output}")
        print(f"  NDCG@{k} = {ndcg_output}")
        print(f"  SortCons Top-{k} = {calculate_sortcons(evaluation_ranking[:k]):.3f}")


def main(argv=None):
    args = build_argument_parser().parse_args(argv)
    movies = movie_service.load_movies()
    if not movies:
        print("Dataset gagal dimuat.")
        return

    prompt = ''
    if not args.queries:
        prompt = input(
            "Tulis query pencarian film (pisahkan beberapa query dengan '|', "
            "mis. warkop dki | film horor): "
        )
    queries = normalize_queries(args.queries, prompt)
    if not queries:
        print("Query pencarian wajib diisi.")
        return

    k_list = [5, 10, 20]
    for query in queries:
        evaluate_query(query, movies, k_list)


if __name__ == "__main__":
    main()
