import math
import sys
import types

import numpy as np
from app.movie_service import movie_service
import precision_ndcg_by_tab
from precision_ndcg_by_tab import is_relevant
from precision_ndcg_by_tab import (
    calculate_ranking_metrics,
    calculate_sortcons,
    evaluate_query,
    find_exact_reference_movie,
    get_content_ranking,
    ndcg_at_k,
    normalize_queries,
    precision_at_k,
    relevance_grade,
)


def test_shared_genre_alone_is_not_relevant():
    query_movie = {
        'id': 1,
        'title': 'Alpha Beta',
        'overview': 'A story about a distant planet.',
        'genres': [{'name': 'Drama'}],
    }
    candidate = {
        'id': 2,
        'title': 'Unrelated Mystery',
        'overview': 'A documentary about ocean wildlife.',
        'genres': [{'name': 'Drama'}],
    }

    assert not is_relevant(query_movie, candidate)


def test_weak_fuzzy_title_similarity_and_shared_genre_are_not_relevant():
    query_movie = {
        'id': 1,
        'title': 'Dilan 1990',
        'overview': 'A high school romance in Bandung.',
        'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
    }
    candidate = {
        'id': 2,
        'title': 'Nikah Duluan',
        'overview': 'A family prepares for a wedding.',
        'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
    }
    substring_candidate = {
        'id': 3,
        'title': 'Keadilan',
        'overview': 'A courtroom case changes a family.',
        'genres': [{'name': 'Drama'}, {'name': 'Romance'}],
    }

    assert not is_relevant(query_movie, candidate)
    assert not is_relevant(query_movie, substring_candidate)


def test_one_shared_title_word_is_not_enough_for_title_relevance():
    cases = [
        (
            {'id': 1, 'title': 'Pengabdi Setan'},
            {'id': 2, 'title': 'Pengabdi Sultan'},
        ),
        (
            {'id': 3, 'title': 'Laskar Pelangi'},
            {'id': 4, 'title': 'Merangkai Pelangi'},
        ),
        (
            {'id': 5, 'title': 'Pengabdi Setan 2'},
            {'id': 6, 'title': 'Pengabdi Sultan 3'},
        ),
    ]

    for query_movie, candidate in cases:
        assert movie_service.get_relevance_status(
            query_movie, candidate
        ) == (False, '')


def test_complete_title_phrase_and_numbered_sequel_remain_relevant():
    query_movie = {'id': 1, 'title': 'Ocean Signal'}
    sequel = {'id': 2, 'title': 'Ocean Signal: The Return'}
    numbered_sequel = {'id': 3, 'title': 'Dilan 1990'}
    numbered_follow_up = {'id': 4, 'title': 'Dilan 1991'}
    dilan_reference = {'id': 7, 'title': 'Dilan 1990'}

    assert movie_service.get_relevance_status(query_movie, sequel)[0]
    assert movie_service.get_relevance_status(
        dilan_reference, numbered_follow_up
    ) == (True, 'Mirip berdasarkan judul')


def test_missing_synopsis_uses_same_director_and_shared_genre_as_evidence():
    query_movie = {
        'id': 1,
        'title': 'Komang',
        'overview': '',
        'director': 'Naya Anindita',
        'genres': [{'name': 'Drama'}, {'name': 'Percintaan'}],
    }
    same_director_and_genre = {
        'id': 2,
        'title': 'Eggnoid',
        'overview': 'A young woman encounters a mysterious android.',
        'director': 'Naya Anindita',
        'genres': [{'name': 'Drama'}, {'name': 'Percintaan'}],
    }
    same_director_different_genre = {
        'id': 3,
        'title': 'Different genre',
        'director': 'Naya Anindita',
        'genres': [{'name': 'Horror'}],
    }

    assert movie_service.get_relevance_status(
        query_movie, same_director_and_genre
    ) == (True, 'Mirip berdasarkan genre dan sutradara')
    assert not is_relevant(query_movie, same_director_different_genre)


def test_recommendations_prioritize_title_then_synopsis_then_genre_and_director(
    monkeypatch,
):
    service = movie_service.__class__()
    movies = [
        {
            'id': 1,
            'title': 'Ocean Signal',
            'overview': 'A marine scientist finds a signal in the ocean.',
            'genres': [{'name': 'Adventure'}],
            'director': 'A. Director',
        },
        {
            'id': 2,
            'title': 'Ocean Signal: The Return',
            'overview': 'A family prepares for a wedding.',
            'genres': [{'name': 'Drama'}],
            'director': 'Another Director',
        },
        {
            'id': 3,
            'title': 'The Deep Current',
            'overview': 'A researcher discovers an underwater message.',
            'genres': [{'name': 'Drama'}],
            'director': 'Another Director',
        },
        {
            'id': 4,
            'title': 'A Quiet Wedding',
            'overview': 'A family prepares for a wedding.',
            'genres': [{'name': 'Adventure'}],
            'director': 'A. Director',
        },
    ]
    monkeypatch.setattr(
        service,
        '_get_semantic_similarity_scores',
        lambda candidate_movies, references: np.array([1.0, 0.1, 0.8, 0.1]),
    )

    recommendations = service._recommend_content_similar(
        [0], movies, top_n=4, include_references=True
    )

    assert [movie['id'] for movie in recommendations] == [1, 2, 3, 4]
    assert recommendations[1]['relevance'] == 'Mirip berdasarkan judul'
    assert recommendations[2]['relevance'] == 'Mirip berdasarkan sinopsis'
    assert recommendations[3]['relevance'] == (
        'Mirip berdasarkan genre dan sutradara'
    )


def test_semantic_synopsis_similarity_can_make_a_candidate_relevant():
    query_movie = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine biologist discovers a signal under the ocean.',
        'genres': [{'name': 'Adventure'}],
    }
    candidate = {
        'id': 2,
        'title': 'The Deep Current',
        'overview': 'A scientist investigates a mysterious underwater message.',
        'genres': [{'name': 'Adventure'}],
        'semantic_similarity': 0.8,
    }

    assert is_relevant(query_movie, candidate)
    assert movie_service.get_relevance_status(
        query_movie, candidate, semantic_similarity=0.8
    ) == (True, 'Mirip berdasarkan sinopsis dan genre')


def test_tfidf_synopsis_evidence_is_not_discarded_when_semantic_score_is_below_threshold():
    query_movie = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine scientist discovers an ancient signal beneath the ocean.',
    }
    candidate = {
        'id': 2,
        'title': 'The Deep Current',
        'overview': 'A marine scientist investigates a signal beneath the ocean.',
    }

    assert movie_service.get_relevance_status(
        query_movie,
        candidate,
        semantic_similarity=0.4,
        synopsis_similarity=0.2,
    ) == (True, 'Mirip berdasarkan sinopsis')


def test_matching_director_is_included_with_synopsis_and_genre_evidence():
    query_movie = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine biologist discovers an ancient signal beneath the Pacific ocean.',
        'genres': [{'name': 'Adventure'}],
        'director': 'A. Director',
    }
    candidate = {
        'id': 2,
        'title': 'The Forgotten Expedition',
        'overview': 'A scientist discovers a signal beneath the ocean.',
        'genres': [{'name': 'Adventure'}],
        'director': 'a. director',
    }

    assert movie_service.get_relevance_status(
        query_movie,
        candidate,
        semantic_similarity=0.8,
    ) == (
        True,
        'Mirip berdasarkan sinopsis, genre, dan sutradara',
    )


def test_tfidf_synopsis_fallback_can_label_synopsis_similarity():
    query_movie = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine biologist discovers an ancient signal beneath the Pacific ocean.',
        'genres': [{'name': 'Adventure'}],
    }
    candidate = {
        'id': 2,
        'title': 'The Forgotten Expedition',
        'overview': 'A marine biologist discovers a signal beneath the ocean.',
        'genres': [{'name': 'Drama'}],
    }
    service = movie_service.__class__()
    service._semantic_model_unavailable = True
    movies = [query_movie, candidate]

    recommendations = service._recommend_content_similar(
        [0], movies, top_n=2, include_references=True
    )

    assert len(recommendations) == 2
    assert 'sinopsis' in recommendations[1]['relevance']
    assert movie_service.get_relevance_status(
        query_movie,
        candidate,
        synopsis_similarity=0.063,
    ) == (False, '')


def test_missing_or_placeholder_synopses_cannot_prove_synopsis_similarity():
    query_movie = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'Belum tersedia',
    }
    candidate = {
        'id': 2,
        'title': 'Different Story',
        'overview': 'Belum tersedia',
    }

    assert movie_service.get_relevance_status(
        query_movie,
        candidate,
        synopsis_similarity=1.0,
    ) == (False, '')
    assert movie_service._get_movie_search_terms(candidate)['overview'] == ''


def test_dilan_title_substring_is_included_as_low_confidence_match():
    service = movie_service.__class__()
    movies = [
        {'id': 1, 'title': 'Dilan 1990', 'overview': 'A high school romance.'},
        {'id': 2, 'title': 'Keadilan', 'overview': 'A courtroom story.'},
        {'id': 3, 'title': 'Ocean Signal', 'overview': 'A marine discovery.'},
    ]

    results = service.recommend_similar_movies('dilan', movies, top_n=20)

    keadilan = next(movie for movie in results if movie['id'] == 2)
    assert keadilan['relevance'] == (
        'Kecocokan rendah berdasarkan judul sebagian'
    )


def test_komang_search_does_not_treat_fuzzy_title_similarity_as_a_match():
    service = movie_service.__class__()
    movies = [
        {'id': 1, 'title': 'Komang', 'overview': 'A story about a singer.'},
        {'id': 2, 'title': 'Kangen', 'overview': 'A story about family.'},
        {'id': 3, 'title': 'kOsOng', 'overview': 'An animated documentary.'},
        {'id': 4, 'title': 'Ocean Signal', 'overview': 'A marine discovery.'},
    ]

    results = service.search_movies('komang', movies)

    assert [movie['id'] for movie in results] == [1]


def test_semantic_score_is_used_by_ranking_metrics():
    query = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine biologist discovers a signal under the ocean.',
        'genres': [{'name': 'Adventure'}],
    }
    candidate = {
        'id': 2,
        'title': 'The Deep Current',
        'overview': 'A scientist investigates a mysterious underwater message.',
        'genres': [{'name': 'Adventure'}],
        'semantic_similarity': 0.8,
    }

    metrics = calculate_ranking_metrics([candidate], query, [1])

    assert metrics['P@1'] == 1.0
    assert metrics['NDCG@1'] == 1.0


def test_semantic_similarity_encoder_scores_synopsis_meaning(monkeypatch):
    class FakeSentenceTransformer:
        def __init__(self, model_name):
            assert model_name == (
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
            )

        def get_sentence_embedding_dimension(self):
            return 2

        def encode(self, texts, **kwargs):
            assert kwargs['normalize_embeddings'] is True
            vectors = {
                'a marine scientist finds a signal': [1.0, 0.0],
                'an underwater message is discovered': [0.8, 0.6],
            }
            return np.array([vectors[text] for text in texts], dtype=np.float32)

    monkeypatch.setitem(
        sys.modules,
        'sentence_transformers',
        types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )
    service = movie_service.__class__()
    movies = [
        {
            'id': 1,
            'title': 'Ocean Signal',
            'overview': 'A marine scientist finds a signal',
        },
        {
            'id': 2,
            'title': 'The Deep Current',
            'overview': 'An underwater message is discovered',
        },
    ]

    scores = service._get_semantic_similarity_scores(movies, [0])

    assert np.allclose(scores, [1.0, 0.8])


def test_missing_reference_synopsis_skips_semantic_model(monkeypatch):
    service = movie_service.__class__()
    monkeypatch.setattr(
        service,
        '_get_movie_search_terms',
        lambda movie: {'overview': movie.get('overview', '')},
    )
    movies = [
        {'id': 1, 'title': 'Komang', 'overview': ''},
        {'id': 2, 'title': 'Candidate', 'overview': 'A film synopsis.'},
    ]

    scores = service._get_semantic_similarity_scores(movies, [0])

    assert scores is None
    assert service._semantic_model is None


def test_semantic_scores_drive_recommendation_badges_and_order(monkeypatch):
    service = movie_service.__class__()
    movies = [
        {
            'id': 1,
            'title': 'Ocean Signal',
            'overview': 'A marine scientist finds a signal in the ocean.',
            'genres': [{'name': 'Adventure'}],
        },
        {
            'id': 2,
            'title': 'The Deep Current',
            'overview': 'An underwater message is discovered by a researcher.',
            'genres': [{'name': 'Adventure'}],
        },
        {
            'id': 3,
            'title': 'The Wedding',
            'overview': 'A family prepares for a wedding.',
            'genres': [{'name': 'Comedy'}],
        },
    ]
    monkeypatch.setattr(
        service,
        '_get_semantic_similarity_scores',
        lambda candidate_movies, references: np.array([1.0, 0.8, 0.1]),
    )

    recommendations = service._recommend_content_similar(
        [0], movies, top_n=3, include_references=True
    )

    assert [movie['id'] for movie in recommendations] == [1, 2, 3]
    assert recommendations[1]['semantic_similarity'] == 0.8
    assert recommendations[1]['relevance'] == 'Mirip berdasarkan sinopsis dan genre'
    assert recommendations[2]['relevance'].startswith('Kecocokan rendah berdasarkan ')


def test_complete_title_match_remains_relevant():
    query_movie = {
        'id': 1,
        'title': 'Alpha Beta',
        'overview': 'A story about a distant planet.',
        'genres': [{'name': 'Drama'}],
    }
    candidate = {
        'id': 2,
        'title': 'Alpha Beta: The Return',
        'overview': 'A documentary about ocean wildlife.',
        'genres': [{'name': 'Comedy'}],
    }

    assert is_relevant(query_movie, candidate)


def test_same_movie_is_not_relevant_to_itself():
    movie = {'id': 1, 'title': 'Alpha Beta', 'genres': [{'name': 'Drama'}]}

    assert not is_relevant(movie, movie)


def test_precision_at_k_requires_k_results():
    assert precision_at_k([1, 0, 0, 0, 0], 5) == 0.2
    assert precision_at_k([1], 5) is None
    assert precision_at_k([], 5) is None


def test_ndcg_at_k_uses_all_candidates_for_ideal_ranking():
    score = ndcg_at_k([1, 0, 0, 0, 0, 1], 5)
    expected = 1 / (1 + 1 / math.log2(3))

    assert math.isclose(score, expected)


def test_ndcg_is_below_one_when_a_nonrelevant_candidate_ranks_first():
    query = {
        'id': 1,
        'title': 'Alpha Beta',
        'overview': 'A story about a distant planet.',
        'genres': [{'name': 'Drama'}],
    }
    results = [
        {
            'id': 3,
            'title': 'Unrelated Mystery',
            'overview': 'A documentary about ocean wildlife.',
            'genres': [{'name': 'Comedy'}],
        },
        {
            'id': 2,
            'title': 'Alpha Beta: The Return',
            'overview': 'A documentary about ocean wildlife.',
        },
    ]

    metrics = calculate_ranking_metrics(results, query, [2])

    assert metrics['P@2'] == 0.5
    assert 0 < metrics['NDCG@2'] < 1


def test_normalize_queries_accepts_multiple_cli_and_prompt_queries():
    assert normalize_queries(['Dilan 1990', 'Komang']) == ['Dilan 1990', 'Komang']
    assert normalize_queries([], 'Dilan 1990 | Komang') == ['Dilan 1990', 'Komang']
    assert normalize_queries(['Dilan 1990 | Komang']) == ['Dilan 1990', 'Komang']
    assert normalize_queries(['Dilan 1990 | Komang', 'Pengabdi Setan']) == [
        'Dilan 1990',
        'Komang',
        'Pengabdi Setan',
    ]


def test_main_evaluates_each_query(monkeypatch):
    evaluated_queries = []
    monkeypatch.setattr(movie_service, 'load_movies', lambda: [{'title': 'Movie'}])
    monkeypatch.setattr(
        precision_ndcg_by_tab,
        'evaluate_query',
        lambda query, movies, k_list: evaluated_queries.append(query),
    )

    precision_ndcg_by_tab.main(['Dilan 1990 | Komang', 'Pengabdi Setan'])

    assert evaluated_queries == ['Dilan 1990', 'Komang', 'Pengabdi Setan']


def test_content_ranking_sorts_by_pcc_then_popularity(monkeypatch):
    candidates = [
        {
            'id': 1,
            'pcc_similarity': 0.8,
            'popularity': 1,
            'relevance': 'Kecocokan rendah berdasarkan skor konten terdekat',
        },
        {
            'id': 2,
            'pcc_similarity': 0.7,
            'popularity': 1000,
            'relevance': 'Mirip berdasarkan judul',
        },
        {
            'id': 3,
            'pcc_similarity': 0.8,
            'popularity': 50,
            'relevance': 'Mirip berdasarkan judul',
        },
        {
            'id': 4,
            'pcc_similarity': 0.8,
            'popularity': 10,
            'relevance': 'Mirip berdasarkan sinopsis',
        },
    ]
    monkeypatch.setattr(
        movie_service,
        'recommend_similar_movies',
        lambda **kwargs: candidates,
    )
    monkeypatch.setattr(
        movie_service,
        'calculate_pcc_scores',
        lambda query, movies: {
            str(movie['id']): movie['pcc_similarity']
            for movie in movies
        },
    )

    ranking, _ = get_content_ranking('query', [], top_n=4)

    assert [movie['id'] for movie in ranking] == [3, 4, 1, 2]


def test_content_ranking_requests_only_relevant_candidates(monkeypatch):
    captured = {}

    def recommend(**kwargs):
        captured.update(kwargs)
        return [{'id': 1, 'title': 'Candidate', 'popularity': 1}]

    monkeypatch.setattr(movie_service, 'recommend_similar_movies', recommend)
    monkeypatch.setattr(
        movie_service,
        'calculate_pcc_scores',
        lambda query, movies: {'1': 0.5},
    )

    ranking, _ = get_content_ranking('query', [], top_n=20)

    assert len(ranking) == 1
    assert captured['top_n'] == 20


def test_content_ranking_fills_fallback_results_like_search_endpoint(monkeypatch):
    filler_calls = []
    filled_candidate = {'id': 2, 'title': 'Fallback candidate'}

    monkeypatch.setattr(
        movie_service,
        'recommend_similar_movies',
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        movie_service,
        'search_movies',
        lambda query, movies: [],
    )

    def fill_results(query, movies, results, top_n):
        filler_calls.append((query, movies, results, top_n))
        return [filled_candidate]

    monkeypatch.setattr(movie_service, 'fill_search_results', fill_results)
    monkeypatch.setattr(
        movie_service,
        'calculate_pcc_scores',
        lambda query, movies: {'2': 0.4},
    )

    ranking, search_mode = get_content_ranking('query', [], top_n=20)

    assert ranking[0]['id'] == 2
    assert ranking[0]['pcc_similarity'] == 0.4
    assert ranking[0]['relevance'] == (
        'Belum ada kecocokan kuat pada judul, sinopsis, genre, atau sutradara'
    )
    assert search_mode == 'TF-IDF content search fallback'
    assert filler_calls == [('query', [], [], 20)]


def test_legacy_pcc_diagram_uses_shared_web_diagram_generator(monkeypatch):
    import generate_pcc_similarity_diagram
    import generate_search_diagram

    calls = []
    movies = [{'id': 1, 'title': 'Reference'}]
    monkeypatch.setattr(movie_service, 'load_movies', lambda: movies)
    monkeypatch.setattr(
        generate_search_diagram,
        'generate_search_diagram',
        lambda query, loaded_movies, top_n: calls.append(
            (query, loaded_movies, top_n)
        ) or 'generated',
    )

    result = generate_pcc_similarity_diagram.generate_pcc_similarity_diagram(
        'Reference',
        top_n=5,
    )

    assert result == 'generated'
    assert calls == [('Reference', movies, 5)]


def test_content_ranking_does_not_request_low_relevance_candidates(monkeypatch):
    candidates = [{'id': 1, 'title': 'Candidate'}]
    captured = {}

    def recommend(**kwargs):
        captured.update(kwargs)
        return candidates

    monkeypatch.setattr(movie_service, 'recommend_similar_movies', recommend)
    monkeypatch.setattr(
        movie_service,
        'calculate_pcc_scores',
        lambda query, movies: {'1': 0.5},
    )

    get_content_ranking(
        'query',
        [],
        top_n=1,
    )

    assert captured == {'query': 'query', 'movies': [], 'top_n': 1}


def test_exact_reference_resolution_requires_a_full_unambiguous_title():
    movies = [
        {'id': 1, 'title': 'Alpha Beta'},
        {'id': 2, 'title': 'Alpha Gamma'},
    ]

    assert find_exact_reference_movie('Missing title', movies) is None
    assert find_exact_reference_movie('Alpha', movies) is None
    assert find_exact_reference_movie('Alpha Beta', movies) is movies[0]


def test_free_form_query_displays_search_results_without_title_match(
    monkeypatch,
    capsys,
):
    results = [
        {
            'id': 1,
            'title': 'Warkop DKI Reborn 3',
            'genres': [{'name': 'Comedy'}],
            'relevance': 'Mirip berdasarkan judul',
            'pcc_similarity': 0.8,
        },
    ]
    calls = []

    def content_ranking(query, movies, top_n=20):
        calls.append((query, top_n))
        return results, 'Content-Based Filtering'

    monkeypatch.setattr(precision_ndcg_by_tab, 'get_content_ranking', content_ranking)
    evaluate_query('film komedi keluarga', [], [5, 10])

    output = capsys.readouterr().out
    assert calls == [('film komedi keluarga', 20)]
    assert 'Warkop DKI Reborn 3' in output
    assert 'PCC 80.00%' in output
    assert 'tidak menentukan satu film acuan' in output


def test_search_movies_returns_only_genre_matches_for_genre_query():
    movies = [
        {
            'id': 1,
            'title': 'Quiet Journey',
            'overview': 'A family travels across the mountains.',
            'genres': [{'name': 'Comedy'}],
        },
        {
            'id': 2,
            'title': 'Dark Forest',
            'overview': 'A group gets lost in a haunted forest.',
            'genres': [{'name': 'Horror'}],
        },
    ]

    results = movie_service.search_movies('comedy', movies)

    assert [movie['id'] for movie in results] == [1]
    assert results[0]['relevance'] == 'Mirip berdasarkan genre'


def test_ranking_metrics_exclude_query_movie():
    query = {'id': 1, 'title': 'Alpha Beta', 'genres': [{'name': 'Drama'}]}
    results = [
        query,
        {
            'id': 2,
            'title': 'Alpha Beta 2',
            'genres': [{'name': 'Drama'}],
            'relevance': 'Mirip berdasarkan judul',
        },
        {
            'id': 3,
            'title': 'Unrelated',
            'genres': [{'name': 'Comedy'}],
            'relevance': 'Kecocokan rendah',
        },
    ]

    metrics = calculate_ranking_metrics(results, query, [1, 2])

    assert metrics['P@1'] == 1.0
    assert metrics['P@2'] == 0.5


def test_ranking_metrics_use_automatic_relevance_for_precision_and_ndcg():
    query = {
        'id': 1,
        'title': 'Alpha Beta',
        'overview': 'A story about a distant planet.',
        'genres': [{'name': 'Drama'}],
    }
    results = [
        query,
        {
            'id': 2,
            'title': 'Alpha Beta: The Return',
            'overview': 'A documentary about ocean wildlife.',
        },
        {
            'id': 3,
            'title': 'Unrelated Mystery',
            'overview': 'A documentary about ocean wildlife.',
            'genres': [{'name': 'Drama'}],
        },
    ]

    metrics = calculate_ranking_metrics(results, query, [1, 2])

    assert metrics['P@1'] == 1.0
    assert metrics['P@2'] == 0.5
    assert metrics['NDCG@2'] == 1.0


def test_relevance_grade_uses_filmku_title_synopsis_or_genre_director_rule():
    query = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine scientist finds a signal beneath the ocean.',
        'genres': [{'name': 'Adventure'}],
        'director': 'A. Director',
    }

    title_match = {
        'id': 2,
        'title': 'Ocean Signal Returns',
        'overview': 'A family prepares a wedding.',
    }
    synopsis_match = {
        'id': 3,
        'title': 'The Deep Current',
        'overview': 'A marine scientist discovers a signal beneath the ocean.',
        'semantic_similarity': 0.8,
    }
    genre_director_match = {
        'id': 4,
        'title': 'A Quiet Wedding',
        'overview': 'A family prepares a wedding.',
        'genres': [{'name': 'Adventure'}],
        'director': 'a. director',
    }
    genre_only_match = {
        'id': 6,
        'title': 'Unrelated Adventure',
        'overview': 'A documentary about wildlife.',
        'genres': [{'name': 'Adventure'}],
        'relevance': 'Kecocokan berdasarkan genre',
    }
    low_confidence = {
        'id': 5,
        'title': 'Unrelated Mystery',
        'overview': 'A documentary about wildlife.',
        'relevance': 'Kecocokan rendah berdasarkan skor konten terdekat',
    }

    assert relevance_grade(query, title_match) == 1
    assert relevance_grade(query, synopsis_match) == 1
    assert relevance_grade(query, genre_director_match) == 1
    assert relevance_grade(query, genre_only_match) == 0
    assert relevance_grade(query, low_confidence) == 0


def test_genre_only_label_without_director_match_is_not_relevant():
    query = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine scientist finds a signal beneath the ocean.',
        'genres': [{'name': 'Adventure'}],
    }
    genre_only_match = {
        'id': 2,
        'title': 'Unrelated Adventure',
        'overview': 'A documentary about wildlife.',
        'genres': [{'name': 'Adventure'}],
        'relevance': 'Kecocokan berdasarkan genre',
    }
    unrelated = {
        'id': 3,
        'title': 'Unrelated Mystery',
        'overview': 'A documentary about ocean wildlife.',
        'genres': [{'name': 'Comedy'}],
    }

    metrics = calculate_ranking_metrics(
        [genre_only_match, unrelated],
        query,
        [1, 2],
    )

    assert metrics['P@1'] == 0.0
    assert metrics['P@2'] == 0.0
    assert metrics['NDCG@2'] == 0.0
    assert metrics['Relevant@1'] == 0


def test_ndcg_uses_binary_relevance():
    query = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine scientist finds a signal beneath the ocean.',
        'genres': [{'name': 'Adventure'}],
        'director': 'A. Director',
    }
    title_match = {
        'id': 2,
        'title': 'Ocean Signal Returns',
        'overview': 'A family prepares a wedding.',
    }
    synopsis_match = {
        'id': 3,
        'title': 'The Deep Current',
        'overview': 'A marine scientist discovers a signal beneath the ocean.',
        'semantic_similarity': 0.8,
    }

    best_first = calculate_ranking_metrics(
        [title_match, synopsis_match], query, [2]
    )
    weaker_first = calculate_ranking_metrics(
        [synopsis_match, title_match], query, [2]
    )

    assert best_first['P@2'] == weaker_first['P@2'] == 1.0
    assert best_first['NDCG@2'] == 1.0
    assert weaker_first['NDCG@2'] == 1.0


def test_sortcons_checks_the_search_pcc_order():
    ranking = [
        {'id': 1, 'relevance': 'Kecocokan berdasarkan genre',
         'pcc_similarity': 0.8, 'popularity': 1},
        {'id': 2, 'relevance': 'Mirip berdasarkan sinopsis',
         'pcc_similarity': 0.4, 'popularity': 1},
        {'id': 3, 'relevance': 'Mirip berdasarkan sinopsis',
         'pcc_similarity': 0.1, 'popularity': 1},
    ]

    assert calculate_sortcons(ranking) == 1.0
    assert calculate_sortcons(list(reversed(ranking))) == 0.0
    assert calculate_sortcons([ranking[1], ranking[0], ranking[2]]) == 2 / 3


def test_sortcons_uses_popularity_then_weighted_rating_for_rounded_pcc_ties():
    ranking = [
        {
            'pcc_similarity': 0.804,
            'popularity': 10,
            'vote_average': 8,
            'vote_count': 200,
        },
        {
            'pcc_similarity': 0.803,
            'popularity': 5,
            'vote_average': 9,
            'vote_count': 200,
        },
    ]

    assert calculate_sortcons(ranking) == 1.0
    assert calculate_sortcons(list(reversed(ranking))) == 0.0

    weighted_rating_ranking = [
        {
            'pcc_similarity': 0.804,
            'popularity': 5,
            'vote_average': 9,
            'vote_count': 200,
        },
        {
            'pcc_similarity': 0.803,
            'popularity': 5,
            'vote_average': 8,
            'vote_count': 200,
        },
    ]
    assert calculate_sortcons(weighted_rating_ranking) == 1.0
    assert calculate_sortcons(list(reversed(weighted_rating_ranking))) == 0.0
    assert calculate_sortcons([{}]) == 1.0
    assert calculate_sortcons([]) == 1.0


def test_evaluate_query_reports_metrics_for_single_search_ranking(
    monkeypatch,
    capsys,
):
    query_movie = {
        'id': 1,
        'title': 'Ocean Signal',
        'overview': 'A marine scientist finds a signal beneath the ocean.',
    }
    ranking = [
        query_movie,
        {
            'id': 2,
            'title': 'Ocean Signal Returns',
            'overview': 'A family plans a wedding.',
            'release_date': '2020-01-01',
            'vote_average': 8.0,
            'vote_count': 200,
            'popularity': 2,
        },
        {
            'id': 3,
            'title': 'The Deep Current',
            'overview': 'A marine scientist discovers a signal beneath the ocean.',
            'semantic_similarity': 0.8,
            'synopsis_similarity': 0.2,
            'release_date': '2022-01-01',
            'vote_average': 5.0,
            'vote_count': 100,
            'popularity': 20,
        },
    ]
    monkeypatch.setattr(
        precision_ndcg_by_tab,
        'get_content_ranking',
        lambda query, movies, top_n: (ranking, 'Content-Based Filtering'),
    )

    evaluate_query('Ocean Signal', [query_movie], [1, 2])
    output = capsys.readouterr().out

    assert 'URUTAN PENCARIAN PCC' in output
    assert '[Trending]' not in output
    assert '[Newest]' not in output
    assert '[Popular]' not in output
    assert output.count('SortCons Top-') == 2
    assert output.count('Precision@') == 2
    assert output.count('NDCG@') == 2


def test_evaluate_query_preserves_website_ranking_and_metrics(
    monkeypatch,
    capsys,
):
    query_movie = {'id': 1, 'title': 'Ocean Signal'}
    ranking = [query_movie] + [
        {
            'id': movie_id,
            'title': f'Candidate {movie_id}',
            'pcc_similarity': 1 - movie_id / 100,
            'popularity': movie_id,
        }
        for movie_id in range(2, 22)
    ]
    requested_counts = []

    def content_ranking(query, movies, top_n=20):
        requested_counts.append(top_n)
        return ranking[:top_n], 'Content-Based Filtering'

    monkeypatch.setattr(
        precision_ndcg_by_tab,
        'get_content_ranking',
        content_ranking,
    )

    evaluate_query('Ocean Signal', [query_movie], [5, 10, 20])
    output = capsys.readouterr().out

    assert requested_counts == [20, 21]
    assert 'Jumlah hasil: 20' in output
    assert '1. Ocean Signal |' in output
    assert '21. Candidate 21 |' not in output
    for k in (5, 10, 20):
        assert f'Precision@{k} =' in output
        assert f'NDCG@{k} =' in output
        assert f'SortCons Top-{k} =' in output
