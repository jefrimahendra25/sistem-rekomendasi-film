#!/usr/bin/env python3
"""
Generate Trending Tab Diagram
Menampilkan diagram hasil pencarian Trending Tab
Menggunakan TF-IDF + PCC + Trending Score (vote_avg × vote_count / 1000 + new release bonus)
"""

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
        # FILTER BY QUERY (seperti web filter by genre/year)
        # =====================================================

        # Di web, tab trending tidak melakukan search, tapi filter
        # Untuk diagram, kita filter berdasarkan query "dilan 1990"
        # menggunakan search untuk mendapatkan film yang relevan
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
        # SORT BY TRENDING (menggunakan rumus skripsi)
        # =====================================================

        print("\n3. Sorting by trending score (rumus skripsi)...")

        def get_trending_score(movie):
            """Calculate trending score sesuai rumus skripsi.
            
            Rumus 3.2: Engagement Score = (Rating × Vote Count) / 1000
            Rumus 3.3: Recency Bonus = (30 - Days Since Release) × 0.1 (jika Days ≤ 30)
            Rumus 3.4: Trending Score = Engagement Score + Recency Bonus
            """
            vote_avg = movie.get('vote_average', 0) or 0
            vote_count = movie.get('vote_count', 0) or 0
            
            # Engagement Score (Rumus 3.2)
            engagement_score = (vote_avg * vote_count) / 1000
            
            # Recency Bonus (Rumus 3.3)
            recency_bonus = 0.0
            release_date = movie.get('release_date', '')
            if release_date:
                try:
                    rd_dt = datetime.strptime(release_date, '%Y-%m-%d')
                    days_since_release = (datetime.now() - rd_dt).days
                    if days_since_release <= 30:
                        recency_bonus = (30 - days_since_release) * 0.1
                except (ValueError, TypeError):
                    pass
            
            # Trending Score (Rumus 3.4)
            trending_score = engagement_score + recency_bonus
            
            return trending_score

        # Sort by trending score descending
        trending_results = sorted(filtered_results, key=get_trending_score, reverse=True)

        # =====================================================
        # HASIL DINAMIS
        # =====================================================

        top_movies = trending_results

        total_movies = len(top_movies)

        print(f"   Total trending movies : {total_movies}")

        # =====================================================
        # EXTRACT DATA
        # =====================================================

        titles = []
        trending_scores = []
        vote_averages = []
        vote_counts = []

        for movie in top_movies:

            title = movie.get('title', 'Unknown')

            # Potong judul terlalu panjang
            if len(title) > 35:
                title = title[:35] + '...'

            titles.append(title)

            # Gunakan trending score (rumus skripsi)
            trending_scores.append(get_trending_score(movie))

            vote_averages.append(float(movie.get('vote_average', 0)))
            vote_counts.append(int(movie.get('vote_count', 0)))

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
        fig.subplots_adjust(left=0.38, right=0.80, top=0.86, bottom=0.20)

        # =====================================================
        # Y POSITION
        # =====================================================

        y_pos = np.arange(len(titles))

        # =====================================================
        # HORIZONTAL BAR CHART WITH LOG SCALE
        # =====================================================

        plot_scores = []
        for score in trending_scores:
            # Bulatkan ke 2 desimal untuk konsistensi
            rounded_score = round(score, 2)

            if rounded_score == 0:
                plot_scores.append(0.01)  # Bar pendek untuk nilai 0
            elif rounded_score == 0.01:
                plot_scores.append(0.012)  # Bar sedikit lebih panjang untuk nilai 0.01
            elif rounded_score == 0.02:
                plot_scores.append(0.02)  # Bar untuk nilai 0.02
            elif rounded_score == 0.03:
                plot_scores.append(0.03)  # Bar untuk nilai 0.03
            elif rounded_score == 0.04:
                plot_scores.append(0.04)  # Bar untuk nilai 0.04
            else:
                plot_scores.append(max(score, 0.01))

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

        max_score = max(plot_scores) if plot_scores else 1
        x_limit = max_score * 1.25 if max_score > 0 else 1

        for i, (score, bar) in enumerate(zip(trending_scores, bars)):
            width = bar.get_width()
            
            if score <= 0.04:
                # Untuk nilai kecil, tempatkan label lebih dekat dengan bar
                label_x = width * 1.02
                ha = 'left'
                label_color = '#222222'
            else:
                label_x = width * 1.06 if width > 0.05 else width + 0.03
                ha = 'left'
                label_color = '#222222'

                if label_x >= x_limit:
                    label_x = width * 0.92
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
        ax.set_xscale('log')
        ax.set_xlim(0.01, x_limit)

        # =====================================================
        # TITLE
        # =====================================================

        fig.suptitle(
            f'Hasil Film Trending Berdasarkan Query "{query}"',
            fontsize=22,
            fontweight='bold',
            y=0.98
        )

        ax.set_title(
            'Top 20 film teratas berdasarkan trending score (log scale)',
            fontsize=12,
            color='#444444',
            pad=24,
            loc='left'
        )

        # =====================================================
        # AXIS LABEL
        # =====================================================

        ax.set_xlabel(
            'Trending Score [skala log]',
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
        ax.xaxis.set_major_locator(mticker.LogLocator(base=10.0, subs=(1.0, 2.0, 5.0), numticks=10))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))

        # =====================================================
        # INFO BOX
        # =====================================================

        info_text = (
            f"Total Film : {len(titles)}\n"
            "Source : TMDb Dataset\n"
            "Search : TF-IDF + PCC\n"
            "Sorting : Trending Score (Rumus Skripsi)"
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

        png_file = f'trending_tab_{query.replace(" ", "_")}.png'

        pdf_file = f'trending_tab_{query.replace(" ", "_")}.pdf'

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
