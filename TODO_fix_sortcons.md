# TODO: Fix SortCons Calculation untuk Tab Trending

## Masalah
SortCons menggunakan `popularity` sebagai sort key untuk tab `trending`, tapi backend `_sort_trending` menggunakan rumus:
```
score = (vote_avg * vote_count) / 1000 + recency_bonus
```
Ini menyebabkan SortCons tidak akurat.

## Steps:
- [x] 1. Analisis kode dan identifikasi mismatch
- [x] 2. Dapatkan persetujuan user

### File: `precision_ndcg_by_tab.py`
- [x] 3. Fix `get_sort_key_for_tab('trending')` — gunakan rumus `_sort_trending` (via `get_trending_score()`)
- [x] 4. Fix `get_tab_ranking_from_candidates('trending')` — gunakan rumus `_sort_trending` (via `get_trending_score()`)

### File: `app/static/js/main.js`
- [x] 5. Fix `displaySearchResults` sorting untuk tab `trending` — gunakan rumus yang konsisten dengan backend

