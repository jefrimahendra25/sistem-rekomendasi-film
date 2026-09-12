from app.movie_service import movie_service
from app.utils import paginate_movies

import math
from random import Random
from typing import List, Dict
from datetime import datetime


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

    return SequenceMatcher(
        None,
        str(text1).lower(),
        str(text2).lower(),
    ).ratio()


def is_relevant(query_movie: Dict, movie: Dict) -> bool:
    """Menentukan relevansi (identik dengan precision_search.py)."""
    query_genres = get_genres(query_movie)
    movie_genres = get_genres(movie)

    common_genres = query_genres.intersection(movie_genres)
    genre_match = len(common_genres) > 0

    title_similarity = similarity(
        query_movie.get('title', ''),
        movie.get('title', ''),
    )

    overview_similarity = similarity(
        query_movie.get('overview', '')[:500],
        movie.get('overview', '')[:500],
    )

    query_words = set(query_movie.get('title', '').lower().split())
    movie_words = set(movie.get('title', '').lower().split())

    keyword_match = len(query_words.intersection(movie_words)) > 0

    if genre_match:
        return True

    if title_similarity >= 0.5:
        return True

    if keyword_match:
        return True

    if overview_similarity >= 0.3:
        return True

    return False


def precision_at_k(relevance_scores: List[int], k: int) -> float:
    scores = relevance_scores[:k]

    if len(scores) == 0:
        return 0.0

    return sum(scores) / len(scores)


def calculate_ndcg(relevance_scores: List[int]) -> float:
    dcg = 0.0

    for i, rel in enumerate(relevance_scores):
        dcg += rel / math.log2(i + 2)

    ideal_scores = sorted(relevance_scores, reverse=True)

    idcg = 0.0
    for i, rel in enumerate(ideal_scores):
        idcg += rel / math.log2(i + 2)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def ndcg_at_k(relevance_scores: List[int], k: int) -> float:
    return calculate_ndcg(relevance_scores[:k])


def get_trending_score(movie: Dict) -> float:
    """Menghitung trending score sesuai rumus di skripsi.
    
    Rumus 3.2: Engagement Score = (Rating × Vote Count) / 1000
    Rumus 3.3: Recency Bonus = (30 - Days Since Release) × 0.1 (jika Days ≤ 30)
    Rumus 3.4: Trending Score = Engagement Score + Recency Bonus
    """
    vote_avg = movie.get('vote_average', 0) or 0
    vote_count = movie.get('vote_count', 0) or 0
    
    # Engagement Score (Rumus 3.2)
    engagement_score = (vote_avg * vote_count) / 1000
    
    # Recency Bonus (Rumus 3.3)
    recency_bonus = 0.0
    release_date = movie.get('release_date', '')
    if release_date:
        try:
            rd_dt = datetime.strptime(release_date, '%Y-%m-%d')
            days_since_release = (datetime.now() - rd_dt).days
            if days_since_release <= 30:
                recency_bonus = (30 - days_since_release) * 0.1
        except (ValueError, TypeError):
            pass
    
    # Trending Score (Rumus 3.4)
    trending_score = engagement_score + recency_bonus
    
    return trending_score


def get_sort_key_for_tab(movie: Dict, tab_type: str):
    """Mendapatkan nilai yang seharusnya dipakai untuk sorting di tab tertentu."""
    if tab_type == 'trending':
        # Gunakan rumus yang SAMA dengan _sort_trending di movie_service.py
        return get_trending_score(movie)
    elif tab_type == 'newest':
        rd = movie.get('release_date', '')
        if rd:
            try:
                return datetime.strptime(rd, '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        return datetime(1900, 1, 1)
    elif tab_type == 'popular':
        return movie.get('vote_average', 0) or 0
    return 0


def calculate_sorting_consistency(ranking: List[Dict], tab_type: str, k: int) -> float:
    """
    Mengukur seberapa konsisten urutan film sesuai kriteria tab.

    Menghitung fraction of concordant adjacent pairs:
    - Untuk setiap pasangan film berurutan (i, i+1):
      - Cek apakah nilai sort_key film i >= sort_key film i+1
      - Jika ya -> concordant (benar), jika tidak -> discordant (salah)
    - Score = jumlah concordant pairs / total adjacent pairs
    """
    topk = ranking[:k]
    if len(topk) < 2:
        return 1.0  # Jika hanya 1 film, urutan selalu benar

    # Ambil sort key untuk setiap film
    keys = []
    for m in topk:
        key = get_sort_key_for_tab(m, tab_type)
        keys.append(key)

    # Hitung jumlah pasangan berurutan yang benar
    concordant = 0
    total_pairs = len(keys) - 1

    for i in range(len(keys) - 1):
        # Nilai sekarang harus >= nilai berikutnya (karena descending)
        if keys[i] >= keys[i + 1]:
            concordant += 1

    if total_pairs == 0:
        return 1.0

    score = concordant / total_pairs

    # Log detail pelanggaran untuk K=20
    if k >= 20:
        print(f"\n  --- Detail Sorting Consistency ({tab_type}) ---")
        violations = []
        for i in range(len(keys) - 1):
            if not (keys[i] >= keys[i + 1]):
                violations.append((i + 1, i + 2, keys[i], keys[i + 1]))
        if violations:
            print(f"  Ditemukan {len(violations)} pelanggaran urutan:")
            for pos1, pos2, val1, val2 in violations:
                if tab_type == 'newest':
                    y1 = val1.year if hasattr(val1, 'year') else val1
                    y2 = val2.year if hasattr(val2, 'year') else val2
                    print(f"    Posisi {pos1} (tahun {y1}) > Posisi {pos2} (tahun {y2}) -- ❌")
                else:
                    print(f"    Posisi {pos1} ({val1:.3f}) > Posisi {pos2} ({val2:.3f}) -- ❌")
        else:
            print(f"  Semua urutan sesuai kriteria ✅")
        print(f"  Score: {score:.3f} ({concordant}/{total_pairs} pasangan benar)")

    return score


def evaluate_ranking(ranking: List[Dict], query_movie: Dict, k_list: List[int], tab_type: str = ''):
    max_k = max(k_list)
    topk = ranking[:max_k]

    relevance_scores = [1 if is_relevant(query_movie, m) else 0 for m in topk]

    metrics = {}
    for k in k_list:
        metrics[f'P@{k}'] = precision_at_k(relevance_scores, k)
        metrics[f'NDCG@{k}'] = ndcg_at_k(relevance_scores, k)
        if tab_type:
            metrics[f'SortCons@{k}'] = calculate_sorting_consistency(ranking, tab_type, k)

    print(f"\n===== HASIL URUTAN PER TAB (top-{max_k}) =====")
    for rank, movie in enumerate(topk, start=1):
        relevant = is_relevant(query_movie, movie)
        status = "Relevan" if relevant else "Tidak Relevan"

        genres = []
        for g in movie.get('genres', []):
            if isinstance(g, dict):
                genres.append(g.get('name', ''))
            else:
                genres.append(str(g))

        # Tampilkan sort key untuk debugging
        sort_key = get_sort_key_for_tab(movie, tab_type)
        if tab_type == 'trending':
            print(f"{rank}. {movie.get('title')} | {', '.join(genres)} | {status} | Trending Score: {sort_key:.3f}")
        elif tab_type == 'newest':
            year = sort_key.year if hasattr(sort_key, 'year') else 'N/A'
            print(f"{rank}. {movie.get('title')} | {', '.join(genres)} | {status} | Release Year: {year}")
        elif tab_type == 'popular':
            print(f"{rank}. {movie.get('title')} | {', '.join(genres)} | {status} | Vote Avg: {sort_key:.1f}")
        else:
            print(f"{rank}. {movie.get('title')} | {', '.join(genres)} | {status}")

    return metrics


def pick_query_movie_via_search(movies: List[Dict]):
    """Input judul -> search_movies -> ambil search_results[0]."""
    print("\n=== PILIH QUERY FILM (mengikuti precision_search.py) ===")
    user_in = input("Tulis judul film (mis. Dilan 1990): ").strip()

    if not user_in:
        return None

    search_results = movie_service.search_movies(user_in, movies)
    if not search_results:
        print("Tidak ada hasil search untuk input tersebut.")
        return None

    query_movie = search_results[0]
    print(f"Query Movie (dipilih dari top search): {query_movie.get('title')}")
    return query_movie


def get_tab_ranking_from_candidates(
    base_candidates: List[Dict],
    tab_type: str,
    *,
    genre_id: str = '',
    year: str = '',
    page: int = 1,
    limit: int = 20,
    show_all: bool = False,
):
    """Ambil ranking tab dari kandidat. Sorting disamakan dengan sorting
    di backend (_sort_trending / _sort_newest / _sort_popular).

    - trending: urut berdasarkan trending_score = (vote_avg * vote_count)/1000 + recency_bonus (descending)
    - newest:   urut berdasarkan release_date (descending)
    - popular:  urut berdasarkan vote_average (descending)
    """
    filtered = movie_service.filter_movies(base_candidates, genre_id, year)

    if tab_type == 'trending':
        # Gunakan rumus yang SAMA dengan _sort_trending di movie_service.py
        sorted_movies = sorted(filtered, key=get_trending_score, reverse=True)
    elif tab_type == 'newest':
        def _parse_date(m):
            rd = m.get('release_date', '')
            if rd:
                try:
                    return datetime.strptime(rd, '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
            return datetime(1900, 1, 1)
        sorted_movies = sorted(filtered, key=_parse_date, reverse=True)
    elif tab_type == 'popular':
        sorted_movies = sorted(filtered, key=lambda m: m.get('vote_average', 0) or 0, reverse=True)
    else:
        sorted_movies = filtered[:]

    paginated_movies, _, _, _ = paginate_movies(
        sorted_movies,
        page=page,
        items_per_page=limit,
        show_all=show_all,
    )
    return paginated_movies


def split_movies(movies: List[Dict], split_ratio: float = 0.8, seed: int = 42):
    rnd = Random(seed)
    movies_shuffled = movies[:]
    rnd.shuffle(movies_shuffled)
    split_idx = int(len(movies_shuffled) * split_ratio)
    return movies_shuffled[:split_idx], movies_shuffled[split_idx:]


def main():
    movies = movie_service.load_movies()
    if not movies:
        print("Dataset gagal dimuat.")
        return

    _train_movies, _test_movies = split_movies(movies, split_ratio=0.8, seed=42)

    query_movie = pick_query_movie_via_search(movies)
    if not query_movie:
        return

    print(f"\n=== Query yang dipakai: {query_movie.get('title')} ===")

    genre_id = ''
    year = ''
    page = 1
    limit = 20
    show_all = False

    tabs = {
        "trending": "trending",
        "newest": "newest",
        "popular": "popular",
    }

    k_list = [5, 10, 20]

    print("\n=== HASIL EVALUASI PER TAB (Precision@K & NDCG@K & SortCons@K) ===")

    base_candidates = movie_service.search_movies(query_movie.get('title', ''), movies, min_results=20)
    base_candidates = base_candidates[:20]

    for label, tab_type in tabs.items():
        # Semua tab menggunakan hasil search (film relevan dengan query)
        # Tab trending mengurutkan berdasarkan trending score, bukan similarity score
        ranking = get_tab_ranking_from_candidates(
            base_candidates,
            tab_type,
            genre_id=genre_id,
            year=year,
            page=page,
            limit=limit,
            show_all=show_all,
        )

        print(f"\n--- Tab: {label} ---")
        metrics = evaluate_ranking(ranking, query_movie, k_list, tab_type=tab_type)

        for k in k_list:
            print(f"  P@{k}    = {metrics[f'P@{k}']:.3f}")
            print(f"  NDCG@{k} = {metrics[f'NDCG@{k}']:.3f}")
            print(f"  SortCons@{k} = {metrics[f'SortCons@{k}']:.3f}")


if __name__ == "__main__":
    main()

