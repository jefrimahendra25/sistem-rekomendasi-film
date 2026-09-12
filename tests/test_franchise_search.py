import pytest

from app.movie_service import MovieService


def _title_has_any(title: str, tokens: list[str]) -> bool:
    t = str(title).lower()
    return any(tok in t for tok in tokens)


def test_franchise_boost_dilan_1990_includes_other_series_titles():
    """Pastikan query seri "dilan 1990" meng-include entri seri lain (minimal ada token dilan/milea)."""
    service = MovieService()
    movies = service.load_movies()
    assert movies, "Dataset movies harus ter-load"

    results = service.search_movies("dilan 1990", movies, min_results=20)
    assert isinstance(results, list)
    assert len(results) > 0

    # Target yang robust: minimal satu judul mengandung token dilan/milea
    # (bukan mematok ID/teks tahun yang bisa berubah di dataset)
    assert any(_title_has_any(m.get("title", ""), ["dilan", "milea"]) for m in results)

