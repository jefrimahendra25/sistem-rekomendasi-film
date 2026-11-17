import json
import sys

import pytest
import requests

from enrich_movie_metadata import (
    TMDBAuthenticationError,
    _request_tmdb_details,
    apply_metadata,
    fetch_tmdb_metadata,
    main,
)


class FakeTMDBSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.languages = []

    def get(self, url, params, timeout):
        self.languages.append(params['language'])
        return self.responses.pop(0)


def tmdb_response(payload, status_code=200):
    response = requests.Response()
    response.status_code = status_code
    response.headers = {}
    response._content = json.dumps(payload).encode('utf-8')
    return response


def test_local_backfill_uses_exact_ids_and_preserves_existing_metadata():
    movies = [
        {'id': 12, 'overview': '', 'director': 'Existing Director'},
        {'id': 13, 'overview': '', 'director': ''},
    ]
    overrides = {}
    local_metadata = {
        '12': {
            'overview': 'Verified overview',
            'director': 'Different Director',
            'source': 'local.csv',
        },
        '99': {
            'overview': 'Wrong movie',
            'director': 'Wrong director',
            'source': 'local.csv',
        },
    }

    count = apply_metadata(movies, overrides, local_metadata)

    assert count == 1
    assert overrides == {
        '12': {
            'id': '12',
            'overview': 'Verified overview',
            'director': '',
            'overview_language': '',
            'source': 'local.csv',
        }
    }


def test_tmdb_fetch_uses_english_synopsis_fallback_and_credits():
    session = FakeTMDBSession([
        tmdb_response({
            'overview': '',
            'credits': {
                'crew': [
                    {'job': 'Director', 'name': 'Director One'},
                    {'job': 'Writer', 'name': 'Writer One'},
                    {'job': 'Director', 'name': 'Director Two'},
                ],
            },
        }),
        tmdb_response({'overview': 'Verified English synopsis'}),
    ])

    metadata = fetch_tmdb_metadata('123', session, 'test-key')

    assert metadata == {
        'overview': 'Verified English synopsis',
        'director': 'Director One, Director Two',
        'overview_language': 'en-US',
        'source': 'TMDB',
    }
    assert session.languages == ['id-ID', 'en-US']


def test_tmdb_401_explains_v3_api_key_without_exposing_credentials():
    session = FakeTMDBSession([tmdb_response({}, status_code=401)])

    with pytest.raises(TMDBAuthenticationError) as error:
        _request_tmdb_details(session, '123', 'private-test-key', 'id-ID')

    assert 'API Key (v3)' in str(error.value)
    assert 'v4 Read Access Token' in str(error.value)
    assert 'private-test-key' not in str(error.value)


def test_missing_tmdb_key_exits_before_loading_catalog(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['enrich_movie_metadata.py', '--fetch-tmdb', '--limit', '5'])
    monkeypatch.delenv('TMDB_API_KEY', raising=False)
    monkeypatch.setattr('enrich_movie_metadata.load_dotenv', lambda **kwargs: None)

    class UnexpectedMovieService:
        def __init__(self):
            raise AssertionError('Catalog should not load without an API key.')

    monkeypatch.setattr('enrich_movie_metadata.MovieService', UnexpectedMovieService)

    assert main() == 2
    captured = capsys.readouterr()
    assert 'TMDB_API_KEY belum diatur' in captured.err
    assert 'API Key (v3)' in captured.err
    assert 'Traceback' not in captured.err
