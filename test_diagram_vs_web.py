#!/usr/bin/env python3
"""
Test script untuk membandingkan hasil diagram dengan web
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.movie_service import MovieService

movie_service = MovieService()

# Load movies
movies = movie_service.load_movies()
print(f"Total movies loaded: {len(movies)}")

# Test 1: Search "dilan 1990"
query = "dilan 1990"
search_results = movie_service.search_movies(query, movies, min_results=20)
print(f"\n=== SEARCH RESULTS ({len(search_results)} films) ===")
for i, movie in enumerate(search_results[:10], 1):
    print(f"{i}. {movie.get('title')} - Popularity: {movie.get('popularity'):.2f} - Rating: {movie.get('vote_average')} - Votes: {movie.get('vote_count')}")

# Test 2: Sort search results by popularity
popular_sorted = movie_service.sort_movies(search_results, sort_type='popular')
print(f"\n=== SEARCH RESULTS SORTED BY POPULARITY ===")
for i, movie in enumerate(popular_sorted[:10], 1):
    print(f"{i}. {movie.get('title')} - Popularity: {movie.get('popularity'):.2f} - Rating: {movie.get('vote_average')} - Votes: {movie.get('vote_count')}")

# Test 3: Sort search results by trending
trending_sorted = movie_service.sort_movies(search_results, sort_type='trending')
print(f"\n=== SEARCH RESULTS SORTED BY TRENDING ===")
for i, movie in enumerate(trending_sorted[:10], 1):
    vote_avg = movie.get('vote_average', 0)
    vote_count = movie.get('vote_count', 0)
    score = (vote_avg * vote_count) / 1000
    print(f"{i}. {movie.get('title')} - Trending Score: {score:.3f} - Rating: {vote_avg} - Votes: {vote_count}")

# Test 4: Sort ALL movies by popularity (like /movies/popular endpoint)
all_popular = movie_service.sort_movies(movies, sort_type='popular')
print(f"\n=== ALL MOVIES SORTED BY POPULARITY (like /movies/popular) ===")
for i, movie in enumerate(all_popular[:10], 1):
    print(f"{i}. {movie.get('title')} - Popularity: {movie.get('popularity'):.2f} - Rating: {movie.get('vote_average')} - Votes: {movie.get('vote_count')}")

# Test 5: Sort ALL movies by trending (like /movies/trending endpoint)
all_trending = movie_service.sort_movies(movies, sort_type='trending')
print(f"\n=== ALL MOVIES SORTED BY TRENDING (like /movies/trending) ===")
for i, movie in enumerate(all_trending[:10], 1):
    vote_avg = movie.get('vote_average', 0)
    vote_count = movie.get('vote_count', 0)
    score = (vote_avg * vote_count) / 1000
    print(f"{i}. {movie.get('title')} - Trending Score: {score:.3f} - Rating: {vote_avg} - Votes: {vote_count}")
