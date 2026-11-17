"""Backfill missing movie synopses and directors using exact TMDB IDs."""
import argparse
import csv
import os
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from app.movie_service import MovieService
from app.utils import get_movie_metadata_overrides_path


ROOT = Path(__file__).resolve().parent
OVERRIDE_FIELDS = (
    'id',
    'overview',
    'director',
    'overview_language',
    'source',
)
PLACEHOLDERS = {
    '',
    'nan',
    'none',
    'null',
    'belum tersedia',
    'belum diketahui',
    'belum ada sinopsis',
    'plot belum tersedia',
    'plot belum diketahui',
    'unknown',
    'n/a',
    'tidak tersedia',
}
LOCAL_CATALOGS = (
    ('indonesian_movies.csv', ','),
    ('Data/film_indonesia_dengan_sutradara.csv', ','),
    ('Data/film_indonesia_terbaru.csv', ','),
)
TMDB_MOVIE_URL = 'https://api.themoviedb.org/3/movie/{}'


def has_value(value):
    return str(value or '').strip().casefold() not in PLACEHOLDERS


def normalize_id(value):
    normalized = str(value or '').strip()
    if normalized.endswith('.0'):
        normalized = normalized[:-2]
    return normalized


def load_overrides(path):
    if not path.exists():
        return {}
    with path.open(encoding='utf-8-sig', newline='') as file:
        rows = csv.DictReader(file)
        return {
            movie_id: {
                field: str(row.get(field, '') or '').strip()
                for field in OVERRIDE_FIELDS
            }
            for row in rows
            for movie_id in [normalize_id(row.get('id'))]
            if movie_id and (
                has_value(row.get('overview'))
                or has_value(row.get('director'))
            )
        }


def save_overrides(path, overrides):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8-sig',
        newline='',
        dir=path.parent,
        delete=False,
    ) as file:
        temporary_path = Path(file.name)
        writer = csv.DictWriter(file, fieldnames=OVERRIDE_FIELDS)
        writer.writeheader()
        for movie_id in sorted(overrides, key=lambda value: (not value.isdigit(), value)):
            writer.writerow({
                field: overrides[movie_id].get(field, '')
                for field in OVERRIDE_FIELDS
            })
    os.replace(temporary_path, path)


def load_local_metadata():
    metadata = {}
    for relative_path, delimiter in LOCAL_CATALOGS:
        path = ROOT / relative_path
        if not path.exists():
            continue
        frame = pd.read_csv(
            path,
            sep=delimiter,
            encoding='utf-8-sig',
            dtype={'id': str},
            on_bad_lines='skip',
        )
        for row in frame.to_dict('records'):
            movie_id = normalize_id(row.get('id'))
            if not movie_id:
                continue
            existing = metadata.setdefault(movie_id, {
                'id': movie_id,
                'overview': '',
                'director': '',
                'overview_language': '',
                'source': '',
            })
            for field in ('overview', 'director'):
                value = str(row.get(field, '') or '').strip()
                if not has_value(existing[field]) and has_value(value):
                    existing[field] = value
                    existing['source'] = relative_path
    return metadata


def apply_metadata(target_movies, overrides, local_metadata):
    added_fields = 0
    for movie in target_movies:
        movie_id = normalize_id(movie.get('id'))
        if not movie_id:
            continue
        existing_override = overrides.get(movie_id, {})
        local = local_metadata.get(movie_id, {})
        updates = {}
        for field in ('overview', 'director'):
            if (
                has_value(movie.get(field))
                or has_value(existing_override.get(field))
            ):
                continue
            value = local.get(field, '')
            if has_value(value):
                updates[field] = value
        if not updates:
            continue
        override = overrides.setdefault(movie_id, {
            'id': movie_id,
            'overview': '',
            'director': '',
            'overview_language': '',
            'source': '',
        })
        override.update(updates)
        override['source'] = local.get('source', 'local catalog')
        added_fields += len(updates)
    return added_fields


class TMDBAuthenticationError(RuntimeError):
    pass


def _request_tmdb_details(session, movie_id, api_key, language):
    for attempt in range(5):
        response = session.get(
            TMDB_MOVIE_URL.format(movie_id),
            params={
                'api_key': api_key,
                'language': language,
                'append_to_response': 'credits',
            },
            timeout=20,
        )
        if response.status_code == 404:
            return None
        if response.status_code in (401, 403):
            raise TMDBAuthenticationError(
                f'TMDB rejected credentials or access (HTTP {response.status_code}). '
                'Use the TMDB API Key (v3) from Account Settings > API, not a '
                'v4 Read Access Token, and make sure the key is active.'
            )
        if response.status_code == 429 or response.status_code >= 500:
            retry_after = response.headers.get('Retry-After', '')
            try:
                delay = min(float(retry_after), 30.0)
            except (TypeError, ValueError):
                delay = 2 ** attempt
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(
        f'TMDB did not return movie {movie_id} after retries.'
    )


def fetch_tmdb_metadata(movie_id, session, api_key):
    details = _request_tmdb_details(session, movie_id, api_key, 'id-ID')
    if details is None:
        return None

    overview = str(details.get('overview') or '').strip()
    overview_language = 'id-ID' if has_value(overview) else ''
    if not has_value(overview):
        english_details = _request_tmdb_details(
            session, movie_id, api_key, 'en-US'
        )
        if english_details:
            overview = str(english_details.get('overview') or '').strip()
            if has_value(overview):
                overview_language = 'en-US'

    credits = details.get('credits') or {}
    directors = [
        str(person.get('name', '')).strip()
        for person in credits.get('crew', [])
        if person.get('job') == 'Director' and has_value(person.get('name'))
    ]
    return {
        'overview': overview if has_value(overview) else '',
        'director': ', '.join(dict.fromkeys(directors)),
        'overview_language': overview_language,
        'source': 'TMDB',
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            'Fill missing synopsis/director metadata by exact movie ID. '
            'TMDB requests are made only with --fetch-tmdb.'
        )
    )
    parser.add_argument(
        '--fetch-tmdb',
        action='store_true',
        help='Fetch remaining missing metadata from TMDB (requires TMDB_API_KEY).',
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit TMDB requests for a small test run.',
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be a positive number')

    if args.fetch_tmdb:
        load_dotenv(dotenv_path=ROOT / '.env')
        api_key = os.getenv('TMDB_API_KEY', '').strip()
        if not api_key or api_key == 'your_tmdb_api_key_here':
            print(
                'TMDB_API_KEY belum diatur. Tambahkan API Key (v3) ke .env '
                'dengan format TMDB_API_KEY=your_actual_v3_key, atau set '
                '$env:TMDB_API_KEY di PowerShell. Jangan gunakan Read Access '
                'Token (v4).',
                file=sys.stderr,
            )
            return 2

    service = MovieService()
    target_movies = service.load_movies(force_reload=True)
    overrides_path = Path(get_movie_metadata_overrides_path())
    overrides = load_overrides(overrides_path)
    local_metadata = load_local_metadata()
    added_local = apply_metadata(target_movies, overrides, local_metadata)
    save_overrides(overrides_path, overrides)
    print(f'Filled {added_local} fields from local ID-matched catalogs.')

    if not args.fetch_tmdb:
        print('TMDB was not contacted. Use --fetch-tmdb to request missing records.')
        return 0

    pending = [
        movie for movie in target_movies
        if (
            not has_value(movie.get('overview'))
            and not has_value(overrides.get(normalize_id(movie.get('id')), {}).get('overview'))
        ) or (
            not has_value(movie.get('director'))
            and not has_value(overrides.get(normalize_id(movie.get('id')), {}).get('director'))
        )
    ]
    if args.limit is not None:
        pending = pending[:args.limit]

    failures = []
    not_found = 0
    session = requests.Session()
    for index, movie in enumerate(pending, start=1):
        movie_id = normalize_id(movie.get('id'))
        try:
            fetched = fetch_tmdb_metadata(movie_id, session, api_key)
            if fetched is None:
                not_found += 1
            else:
                override = overrides.setdefault(movie_id, {
                    'id': movie_id,
                    'overview': '',
                    'director': '',
                    'overview_language': '',
                    'source': '',
                })
                for field in ('overview', 'director', 'overview_language'):
                    if has_value(fetched.get(field)):
                        override[field] = fetched[field]
                override['source'] = fetched['source']
                save_overrides(overrides_path, overrides)
        except TMDBAuthenticationError as error:
            print(f'Authentication failed: {error}', file=sys.stderr)
            print(
                'Check the effective TMDB_API_KEY in this terminal and .env. '
                'An environment variable takes precedence over .env.',
                file=sys.stderr,
            )
            return 2
        except (requests.RequestException, RuntimeError) as error:
            failures.append((movie_id, type(error).__name__))
        if index % 50 == 0:
            print(f'Processed {index}/{len(pending)} movies.')

    print(
        f'TMDB pass complete: checked {len(pending)}, '
        f'not found {not_found}, failures {len(failures)}.'
    )
    if failures:
        print('Failed movie IDs and error types:', failures[:30])
        return 1
    print(f'Overrides saved to {overrides_path}. Restart the app to reload metadata.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
