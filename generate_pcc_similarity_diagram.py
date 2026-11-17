
#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def generate_pcc_similarity_diagram(query="Dilan 1990", top_n=20):
    """Generate a PCC diagram from the same ranking used by website search."""
    from app.movie_service import movie_service
    from generate_search_diagram import generate_search_diagram

    movies = movie_service.load_movies()
    if not movies:
        raise RuntimeError("Data film gagal dimuat.")

    return generate_search_diagram(query, movies, top_n=top_n)


def generate_diagram(query="Dilan 1990", top_n=20):
    """Backward-compatible entry point for generating the diagram."""
    return generate_pcc_similarity_diagram(query, top_n=top_n)


def main():
    parser = argparse.ArgumentParser(
        description="Membuat diagram PCC dari hasil pencarian website."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="Dilan 1990",
        help="Query pencarian atau judul film acuan.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        choices=range(1, 21),
        default=20,
        help="Jumlah hasil yang ditampilkan (1-20).",
    )
    args = parser.parse_args()

    generate_pcc_similarity_diagram(
        query=args.query,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
