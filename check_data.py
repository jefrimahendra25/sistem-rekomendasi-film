#!/usr/bin/env python3
"""
Check data for 'ada apa dengan cinta' query
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.movie_service import movie_service

# Load movies
movies = movie_service.load_movies()
print(f"Loaded {len(movies)} movies")

# Search for movies
query = "ada apa dengan cinta"
search_results = movie_service.search_movies(query, movies)
print(f"\n=== SEARCH RESULTS ({len(search_results)} movies) ===")
for i, m in enumerate(search_results, 1):
    print(f"{i}. {m.get('title')} - Rating: {m.get('vote_average')}, Votes: {m.get('vote_count')}, Popularity: {m.get('popularity')}")

# Sort by popular
popular_results = movie_service._sort_popular(search_results)
print(f"\n=== POPULAR SORT RESULTS ({len(popular_results)} movies) ===")
for i, m in enumerate(popular_results, 1):
    print(f"{i}. {m.get('title')} - Rating: {m.get('vote_average')}, Votes: {m.get('vote_count')}, Popularity: {m.get('popularity')}")
