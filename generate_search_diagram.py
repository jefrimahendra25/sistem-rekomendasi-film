#!/usr/bin/env python3
"""Generate content-ranked recommendation diagrams for movie queries."""

import argparse
import os
import re
import sys

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))


def generate_search_diagram(query, movies, top_n=20):
    from precision_ndcg_by_tab import (
        calculate_ranking_metrics,
        calculate_sortcons,
        find_reference_movies,
        format_ranking_metrics,
        get_content_ranking,
        is_reference_movie,
        is_relevant,
    )

    reference_movies = find_reference_movies(query, movies)
    if not reference_movies:
        raise ValueError(
            f"Judul acuan '{query}' tidak ditemukan secara unik di dataset. "
            "Gunakan judul film yang tepat."
        )

    results, search_method = get_content_ranking(query, movies, top_n=20)
    if not results:
        raise ValueError(f"Tidak ada hasil pencarian untuk query '{query}'")

    query_movie = reference_movies[0]
    k_list = [5, 10, 20]
    metrics = calculate_ranking_metrics(results, query_movie, k_list)
    metric_summary = (
        f"{format_ranking_metrics(metrics, k_list)}\n"
        f"SortCons: {calculate_sortcons(results):.3f}"
    )
    displayed_results = results[:top_n]

    titles = [
        (str(movie.get("title") or "Unknown")[:52] + "...")
        if len(str(movie.get("title") or "Unknown")) > 55
        else str(movie.get("title") or "Unknown")
        for movie in displayed_results
    ]
    scores = [movie.get("pcc_similarity", 0.0) * 100 for movie in displayed_results]
    positions = np.arange(len(titles))
    colors = [
        "#08306b" if index == 0 else
        "#2171b5" if index == 1 else
        "#4292c6" if index == 2 else
        "#9ecae1"
        for index in range(len(titles))
    ]

    fig_height = max(8, len(titles) * 0.38)
    fig, ax = plt.subplots(figsize=(16, fig_height))
    fig.subplots_adjust(left=0.37, right=0.94, top=0.88, bottom=0.20)
    bars = ax.barh(
        positions,
        scores,
        color=colors,
        edgecolor="none",
        height=0.62,
    )
    ax.invert_yaxis()
    ax.set_yticks(positions)
    ax.set_yticklabels(titles, fontsize=10)
    ax.set_xlim(0, 110)
    ax.set_xlabel("Kemiripan PCC (%)", fontsize=12, fontweight="bold")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(20))
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.grid(axis="x", linestyle="--", alpha=0.25, color="#999999")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#dddddd")
    ax.set_facecolor("#fbfbfb")
    fig.patch.set_facecolor("white")

    for bar, score in zip(bars, scores):
        ax.text(
            min(score + 1.2, 106),
            bar.get_y() + bar.get_height() / 2,
            f"{score:.2f}%",
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color="#222222",
        )

    fig.suptitle(
        f'Hasil Pencarian "{query}"',
        fontsize=21,
        fontweight="bold",
        y=0.97,
    )
    ax.set_title(
        f"{len(displayed_results)} hasil teratas menurut PCC "
        "(popularitas menjadi pemecah nilai seri)",
        fontsize=12,
        color="#444444",
        loc="left",
        pad=18,
    )
    fig.text(
        0.02,
        0.025,
        f"Query evaluasi: {query_movie.get('title', query)}\n"
        f"Metode pencarian: {search_method}\n"
        "Urutan web: PCC tertinggi, lalu popularitas tertinggi.\n"
        f"{metric_summary}",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#333333",
    )

    output_dir = os.path.join(os.path.dirname(__file__), "hasil_diagram")
    os.makedirs(output_dir, exist_ok=True)
    query_slug = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_") or "query"
    base_path = os.path.join(output_dir, f"search_pcc_{query_slug}")
    png_path = f"{base_path}.png"
    pdf_path = f"{base_path}.pdf"
    fig.savefig(png_path, dpi=400, bbox_inches="tight", pad_inches=0.35)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)

    print(f"PNG saved: {png_path}")
    print(f"PDF saved: {pdf_path}")
    for rank, movie in enumerate(displayed_results, start=1):
        if is_reference_movie(query_movie, movie):
            relevance = "Film acuan"
        else:
            relevance = "Relevan" if is_relevant(query_movie, movie) else "Tidak relevan"
        print(
            f"{rank:>2}. {movie.get('title', 'Unknown')} | "
            f"{movie.get('relevance', '')} | "
            f"PCC {movie.get('pcc_similarity', 0.0) * 100:.2f}% | {relevance}"
        )
    print(metric_summary)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Buat diagram rekomendasi berdasarkan kemiripan konten "
            "serta hitung Precision@K dan NDCG@K."
        )
    )
    parser.add_argument(
        "queries",
        nargs="*",
        help='Satu atau beberapa query, contoh: "Dilan 1990" "Pengabdi Setan".',
    )
    parser.add_argument(
        "--top-n",
        type=int,
        choices=range(1, 21),
        default=20,
        metavar="1-20",
        help="Jumlah hasil yang ditampilkan per query (default: 20).",
    )
    args = parser.parse_args()
    queries = args.queries
    if not queries:
        query = input("Masukkan kata kunci film: ").strip()
        if not query:
            parser.error("Kata kunci film tidak boleh kosong.")
        queries = [query]

    from app.movie_service import movie_service

    movies = movie_service.load_movies()
    failed_queries = []
    for query in queries:
        try:
            generate_search_diagram(
                query,
                movies,
                top_n=args.top_n,
            )
        except ValueError as error:
            print(f"Gagal memproses query '{query}': {error}", file=sys.stderr)
            failed_queries.append(query)

    if failed_queries:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
