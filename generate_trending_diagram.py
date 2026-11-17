#!/usr/bin/env python3
"""Generate a diagram of the web's Trending tab."""

import sys
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from datetime import datetime

plt.style.use('ggplot')

# =====================================================
# ADD PROJECT PATH
# =====================================================

sys.path.insert(0, os.path.dirname(__file__))


def generate_trending_diagram():

    try:

        print("\n=== GENERATING TRENDING TAB DIAGRAM ===\n")

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
        # Match /api/movies?type=trending: filter, sort, then take page one.
        # =====================================================

        filtered_movies = movie_service.filter_movies(movies, '', '')
        print(f"\n2. Movies after web filters : {len(filtered_movies)}")

        # =====================================================
        # VALIDASI
        # =====================================================

        if not filtered_movies:

            print("\n❌ No movies found")
            return

        # =====================================================
        # SORT BY TRENDING (same as MovieService and the web tab)
        # =====================================================

        print("\n3. Sorting by trending score...")

        parsed_release_dates = []
        for movie in filtered_movies:
            try:
                parsed_release_dates.append(
                    datetime.strptime(movie.get('release_date', ''), '%Y-%m-%d')
                )
            except (ValueError, TypeError):
                continue

        oldest_release = min(parsed_release_dates) if parsed_release_dates else None
        newest_release = max(parsed_release_dates) if parsed_release_dates else None
        release_date_range = (
            (newest_release - oldest_release).days
            if oldest_release and newest_release else 0
        )
        recency_weight = 1

        def get_trending_score(movie):
            try:
                vote_avg = float(movie.get('vote_average') or 0)
                vote_count = float(movie.get('vote_count') or 0)
            except (TypeError, ValueError):
                vote_avg = 0.0
                vote_count = 0.0

            engagement_score = (vote_avg * vote_count) / 1000
            recency_score = 0.0
            if release_date_range:
                try:
                    release_date = datetime.strptime(movie.get('release_date', ''), '%Y-%m-%d')
                    recency_score = (release_date - oldest_release).days / release_date_range
                except (ValueError, TypeError):
                    pass

            return engagement_score + recency_weight * recency_score

        trending_results = movie_service.sort_movies(filtered_movies, 'trending')

        # =====================================================
        # HASIL DINAMIS
        # =====================================================

        top_movies = trending_results[:20]

        total_movies = len(top_movies)

        print(f"   Total trending movies : {total_movies}")

        # =====================================================
        # EXTRACT DATA
        # =====================================================

        titles = []
        trending_scores = []
        vote_counts = []

        for movie in top_movies:

            title = movie.get('title', 'Unknown')

            # Potong judul terlalu panjang
            if len(title) > 35:
                title = title[:35] + '...'

            titles.append(title)

            trending_scores.append(get_trending_score(movie))

            try:
                vote_counts.append(int(float(movie.get('vote_count') or 0)))
            except (TypeError, ValueError):
                vote_counts.append(0)

        # =====================================================
        # DATA SUDAH DI-SORT SEBELUMNYA
        # =====================================================

        # =====================================================
        # FIGURE SIZE
        # =====================================================

        fig_height = max(10, len(titles) * 0.35)

        fig, ax = plt.subplots(
            figsize=(16, fig_height)
        )
        fig.subplots_adjust(left=0.38, right=0.95, top=0.86, bottom=0.20)

        # =====================================================
        # Y POSITION
        # =====================================================

        y_pos = np.arange(len(titles))

        # =====================================================
        # HORIZONTAL BAR CHART WITH LINEAR SCALE
        # =====================================================

        plot_scores = trending_scores

        bar_colors = [
            '#08306b' if i == 0 else
            '#2171b5' if i == 1 else
            '#4292c6' if i == 2 else
            '#9ecae1'
            for i in range(len(plot_scores))
        ]

        bars = ax.barh(
            y_pos,
            plot_scores,
            color=bar_colors,
            edgecolor='none',
            height=0.62,
            align='center'
        )

        # =====================================================
        # VALUE LABEL
        # =====================================================

        max_score = max(plot_scores) if plot_scores else 0
        x_limit = max_score * 1.15 if max_score > 0 else 1

        for i, (score, bar) in enumerate(zip(trending_scores, bars)):
            width = bar.get_width()
            label_x = width + max_score * 0.015
            ha = 'left'
            label_color = '#222222'
            if label_x >= x_limit:
                label_x = width - max_score * 0.015
                ha = 'right'
                label_color = 'white'

            ax.text(
                label_x,
                bar.get_y() + bar.get_height() / 2,
                f"{score:.2f}",
                va='center',
                ha=ha,
                fontsize=9,
                fontweight='bold',
                color=label_color
            )

        # =====================================================
        # LABEL Y
        # =====================================================

        ax.set_yticks(y_pos)

        ax.set_yticklabels(
            titles,
            fontsize=10,
            color='#222222'
        )

        # =====================================================
        # RANKING TERTINGGI DI ATAS
        # =====================================================

        ax.invert_yaxis()
        ax.set_xlim(0.01, x_limit)

        # =====================================================
        # TITLE
        # =====================================================

        fig.suptitle(
            'Hasil Film Trending pada Tab Web',
            fontsize=22,
            fontweight='bold',
            y=0.98
        )

        ax.set_title(
            '20 film teratas berdasarkan Trending Score',
            fontsize=12,
            color='#444444',
            pad=24,
            loc='left'
        )

        # =====================================================
        # AXIS LABEL
        # =====================================================

        ax.set_xlabel(
            'Trending Score',
            fontsize=13,
            fontweight='bold'
        )

        ax.set_ylabel(
            'Judul Film',
            fontsize=13,
            fontweight='bold'
        )

        # =====================================================
        # GRID
        # =====================================================

        ax.grid(
            axis='x',
            linestyle='--',
            alpha=0.25,
            color='#999999'
        )


        # =====================================================
        # REMOVE BORDER
        # =====================================================

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#dddddd')
        ax.tick_params(axis='x', labelsize=11)
        ax.tick_params(axis='y', labelsize=10)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(6))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))

        # =====================================================
        # INFO BOX
        # =====================================================

        info_text = (
            f"Total Film : {len(titles)}\n"
            "Sumber : Katalog film web\n"
            "Filter : Semua genre dan tahun\n"
            "Skor : Engagement + recency ternormalisasi"
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

        ax.set_facecolor('#fbfbfb')
        fig.patch.set_facecolor('white')

        # =====================================================
        # OUTPUT FILE
        # =====================================================

        output_dir = os.path.join(os.path.dirname(__file__), 'hasil_diagram')
        os.makedirs(output_dir, exist_ok=True)
        png_file = os.path.join(output_dir, 'trending_tab_all_movies.png')
        pdf_file = os.path.join(output_dir, 'trending_tab_all_movies.pdf')

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

        print("\n=== HASIL FILM TRENDING ===\n")

        print(
            f"{'Rank':<6}"
            f"{'Title':<40}"
            f"{'Trending Score':<15}"
            f"{'Rating':<10}"
            f"{'Votes':<10}"
        )

        print("-" * 100)

        for i, (movie, score) in enumerate(zip(top_movies, trending_scores), start=1):

            print(
                f"{i:<6}"
                f"{movie.get('title', 'Unknown')[:40]:<40}"
                f"{score:<15.3f}"
                f"{movie.get('vote_average', 0):<10.1f}"
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

    generate_trending_diagram()
