"""Debug script untuk mengecek SortCons secara detail"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.movie_service import movie_service
from datetime import datetime

def get_trending_score(movie):
    vote_avg = movie.get('vote_average', 0) or 0
    vote_count = movie.get('vote_count', 0) or 0
    score = (vote_avg * vote_count) / 1000
    release_date = movie.get('release_date', '')
    if release_date:
        try:
            rd_dt = datetime.strptime(release_date, '%Y-%m-%d')
            days_since_release = (datetime.now() - rd_dt).days
            if days_since_release <= 30:
                score += (30 - days_since_release) * 0.1
        except:
            pass
    return score

def main():
    movies = movie_service.load_movies()
    print(f'Total movies: {len(movies)}')

    results = movie_service.search_movies('Dilan 1990', movies, min_results=20)
    results = results[:20]

    if not results:
        print('Tidak ada hasil')
        return

    print(f'\n=== Hasil search "Dilan 1990": {len(results)} film ===')

    # Tampilkan detail
    print(f'{"Rank":<6} {"Title":<35} {"vote_avg":<10} {"vote_count":<12} {"popularity":<12} {"TrendingScore":<20}')
    print('-'*95)
    for rank, m in enumerate(results, 1):
        ts = get_trending_score(m)
        pop = m.get('popularity', 0) or 0
        title = (m.get('title') or '')[:33]
        print(f'{rank:<6} {title:<35} {m.get("vote_average",0):<10} {m.get("vote_count",0):<12} {pop:<12.2f} {ts:<20.6f}')

    # Cek SortCons berdasarkan trending score
    scores = [get_trending_score(m) for m in results]
    concordant = 0
    total = len(scores) - 1
    violations = []

    for i in range(len(scores) - 1):
        if scores[i] >= scores[i + 1]:
            concordant += 1
        else:
            violations.append((i, i+1, scores[i], scores[i+1],
                             results[i].get('title'), results[i+1].get('title')))

    print(f'\n=== SortCons Detail (Trending Score) ===')
    if violations:
        print(f'Ditemukan {len(violations)} pelanggaran:')
        for pos1, pos2, v1, v2, t1, t2 in violations:
            print(f'  Posisi {pos1+1} ({t1[:30]}, score={v1:.6f}) < Posisi {pos2+1} ({t2[:30]}, score={v2:.6f}) -- ❌')
    else:
        print(f'Tidak ada pelanggaran. Semua urutan sudah benar berdasarkan trending score.')

    # UJI LAGI: Sort berdasarkan trending score
    print(f'\n=== Urutan ULANG berdasarkan Trending Score (descending) ===')
    sorted_by_trending = sorted(results, key=get_trending_score, reverse=True)
    print(f'{"Rank":<6} {"Title":<35} {"TrendingScore":<20}')
    print('-'*61)
    for rank, m in enumerate(sorted_by_trending, 1):
        ts = get_trending_score(m)
        title = (m.get('title') or '')[:33]
        print(f'{rank:<6} {title:<35} {ts:<20.6f}')

    # Cek SortCons antara urutan asli vs urutan based on trending score
    print(f'\n=== Perbandingan Urutan ===')
    original_order = {m.get('id'): i for i, m in enumerate(results)}
    new_order = {m.get('id'): i for i, m in enumerate(sorted_by_trending)}
    print(f'{"Title":<35} {"Original Rank":<15} {"New Rank":<15} {"Change":<10}')
    print('-'*75)
    for m in results:
        title = (m.get('title') or '')[:33]
        orig = original_order.get(m.get('id'), -1) + 1
        new = new_order.get(m.get('id'), -1) + 1
        change = new - orig
        sign = '+' if change > 0 else ''
        print(f'{title:<35} {orig:<15} {new:<15} {sign}{change:<9}')

    # SortCons untuk popularitas
    print(f'\n=== SortCons Popularity (OLD) ===')
    pop_scores = [m.get('popularity', 0) or 0 for m in results]
    pop_concordant = 0
    for i in range(len(pop_scores) - 1):
        if pop_scores[i] >= pop_scores[i + 1]:
            pop_concordant += 1
    print(f'SortCons (popularity) = {pop_concordant}/{len(pop_scores)-1} = {pop_concordant/(len(pop_scores)-1):.3f}')

if __name__ == '__main__':
    main()

