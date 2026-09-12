#!/usr/bin/env python3
"""
Generate Popular Tab Diagram
Menampilkan diagram hasil pencarian Popular Tab
Menggunakan TF-IDF + PCC + TMDb Weighted Rating
"""

import sys
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

plt.style.use('ggplot')

# =====================================================
# ADD PROJECT PATH
# =====================================================

sys.path.insert(0, os.path.dirname(__file__))


def generate_popularity_diagram():

    try:

        print("\n=== GENERATING POPULAR TAB DIAGRAM ===\n")

        # =====================================================
        # IMPORT MOVIE SERVICE
        # =====================================================

        from app.movie_service import movie_service

        # =====================================================
        # LOAD MOVIES
        # =====================================================

        print("1. Loading movie data...")

        movies = movie_service.load_movies()

        print(f"   Total movies loaded : {len(movies)}")

        # =====================================================
        # FILTER BY QUERY (seperti web filter by genre/year)
        # =====================================================

        # Di web, tab popular melakukan search dengan query
        # Untuk diagram, kita filter berdasarkan query "dilan 1990"
        query = "dilan 1990"

        print(f"\n2. Filtering movies with query : '{query}'")

        # Menggunakan search untuk filter (mirip dengan filter by genre/year di web)
        filtered_results = movie_service.search_movies(
            query=query,
            movies=movies,
            min_results=5
        )

        print(f"   Filtered results found : {len(filtered_results)}")

        # =====================================================
        # VALIDASI
        # =====================================================

        if not filtered_results:

            print("\n❌ No movies found")
            return

        # =====================================================
        # SORT BY POPULAR (menggunakan vote_average seperti di web)
        # =====================================================

        print("\n3. Sorting by vote_average (rating)...")

        # Gunakan vote_average untuk sorting (sama dengan tampilan di web)
        popular_results = sorted(filtered_results, key=lambda x: x.get('vote_average', 0) or 0, reverse=True)

        # =====================================================
        # HASIL DINAMIS
        # =====================================================

        top_movies = popular_results[:20]

        total_movies = len(top_movies)

        print(f"   Total popular movies : {total_movies}")

        # =====================================================
        # EXTRACT DATA
        # =====================================================

        titles = []
        scores = []
        vote_counts = []

        for movie in top_movies:

            title = movie.get('title', 'Unknown')

            # Potong judul terlalu panjang
            if len(title) > 35:
                title = title[:35] + '...'

            titles.append(title)

            # Gunakan vote_average (rating) untuk scores
            scores.append(
                float(movie.get('vote_average', 0) or 0.0)
            )

            vote_counts.append(
                int(movie.get('vote_count', 0))
            )

        # =====================================================
        # SORT DESCENDING (sudah di-sort sebelumnya, tapi untuk keamanan)
        # =====================================================

        combined = list(zip(titles, scores, vote_counts))

        combined.sort(
            key=lambda x: x[1],
            reverse=True
        )

        titles, scores, vote_counts = zip(*combined)

        # =====================================================
        # FIGURE SIZE
        # =====================================================

        fig_height = max(10, len(titles) * 0.35)

        fig, ax = plt.subplots(
            figsize=(16, fig_height)
        )
        fig.subplots_adjust(left=0.38, right=0.95, top=0.86, bottom=0.20)

        # =====================================================
        # HORIZONTAL BAR CHART WITH LINEAR SCALE
        # =====================================================

        y_pos = np.arange(len(titles))

        bar_colors = [
            '#08306b' if i == 0 else
            '#2171b5' if i == 1 else
            '#4292c6' if i == 2 else
            '#cccccc' if score == 0 else
            '#9ecae1'
            for i, score in enumerate(scores)
        ]

        bars = ax.barh(
            y_pos,
            scores,
            color=bar_colors,
            edgecolor='none',
            height=0.62,
            align='center'
        )

        max_score = max(scores) if scores else 10
        x_limit = max_score * 1.15

        for i, (score, bar) in enumerate(zip(scores, bars)):
            width = bar.get_width()
            if score > 0:
                label_x = width + 0.15
                ha = 'left'
                label_color = '#222222'
            else:
                label_x = 0.1
                ha = 'left'
                label_color = '#888888'

            if label_x >= x_limit:
                label_x = width - 0.15
                ha = 'right'
                label_color = 'white'

            ax.text(
                label_x,
                bar.get_y() + bar.get_height() / 2,
                f"{score:.1f}",
                va='center',
                ha=ha,
                fontsize=9,
                fontweight='bold',
                color=label_color
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(
            titles,
            fontsize=10,
            color='#222222'
        )
        ax.invert_yaxis()
        ax.set_xlim(0, x_limit)
        ax.grid(axis='x', linestyle='--', alpha=0.25, color='#999999')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#dddddd')
        ax.tick_params(axis='x', labelsize=11)
        ax.tick_params(axis='y', labelsize=10)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(1.0))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))

        ax.set_xlabel(
            'Rating (vote_average)',
            fontsize=13,
            fontweight='bold'
        )
        ax.set_ylabel(
            'Judul Film',
            fontsize=13,
            fontweight='bold'
        )

        fig.suptitle(
            f'Hasil Film Populer Berdasarkan Query "{query}"',
            fontsize=22,
            fontweight='bold',
            y=0.98
        )

        ax.set_title(
            'Top 20 film teratas berdasarkan rating (vote_average)',
            fontsize=12,
            color='#444444',
            pad=24,
            loc='left'
        )

        ax.set_facecolor('#fbfbfb')
        fig.patch.set_facecolor('white')

        # =====================================================
        # INFO BOX
        # =====================================================

        info_text = (
            f"Total Film : {len(titles)}\n"
            "Source : TMDb Dataset\n"
            "Search : TF-IDF + PCC\n"
            "Sorting : Popular Tab (vote_average)"
        )

        fig.text(
            0.02,
            0.03,
            info_text,
            ha='left',
            va='bottom',
            fontsize=9,
            color='#333333',
            bbox=dict(
                boxstyle='round,pad=0.4',
                facecolor='white',
                edgecolor='gray',
                alpha=0.92
            )
        )

        # =====================================================
        # LAYOUT
        # =====================================================

        # =====================================================
        # OUTPUT FILE
        # =====================================================

        png_file = f'popular_tab_{query.replace(" ", "_")}.png'

        pdf_file = f'popular_tab_{query.replace(" ", "_")}.pdf'

        # =====================================================
        # SAVE PNG
        # =====================================================

        plt.savefig(
            png_file,
            dpi=300,
            bbox_inches='tight',
            pad_inches=0.5
        )

        print(f"\n✅ PNG saved : {png_file}")

        # =====================================================
        # SAVE PDF
        # =====================================================

        plt.savefig(
            pdf_file,
            bbox_inches='tight',
            pad_inches=0.5
        )

        print(f"✅ PDF saved : {pdf_file}")

        # =====================================================
        # SHOW PLOT
        # =====================================================

        plt.show()

        # =====================================================
        # CLOSE
        # =====================================================

        plt.close()

        # =====================================================
        # PRINT RESULT
        # =====================================================

        print("\n=== HASIL FILM POPULER ===\n")

        print(
            f"{'Rank':<6}"
            f"{'Title':<40}"
            f"{'Rating':<12}"
            f"{'Votes':<10}"
        )

        print("-" * 90)

        for i, movie in enumerate(top_movies, start=1):

            print(
                f"{i:<6}"
                f"{movie.get('title', 'Unknown')[:40]:<40}"
                f"{movie.get('vote_average', 0):<12.1f}"
                f"{movie.get('vote_count', 0):<10}"
            )

        print("\n✅ Diagram generation completed successfully!\n")

    except Exception as e:

        print(f"\n❌ ERROR : {e}")

        import traceback
        traceback.print_exc()


# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':

    generate_popularity_diagram()