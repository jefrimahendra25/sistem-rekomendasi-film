#!/usr/bin/env python3
"""
Generate Newest Tab Diagram
Menampilkan diagram hasil pencarian Newest Tab
Menggunakan TF-IDF + PCC + Newest Score (berdasarkan tanggal rilis terbaru)
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


def generate_newest_diagram():

    try:

        print("\n=== GENERATING NEWEST TAB DIAGRAM ===\n")

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
        # QUERY
        # =====================================================

        query = "dilan 1990"

        print(f"\n2. Searching movies with query : '{query}'")

        # Menggunakan search asli seperti web
        search_results = movie_service.search_movies(
            query=query,
            movies=movies,
            min_results=5
        )

        print(f"   Search results found : {len(search_results)}")

        # =====================================================
        # VALIDASI
        # =====================================================

        if not search_results:

            print("\n❌ No movies found")
            return

        # =====================================================
        # SORT BY NEWEST (menggunakan release_date seperti web)
        # =====================================================

        print("\n3. Sorting by release date (newest first)...")

        # Sort berdasarkan release_date field (seperti di movie_service.py)
        def get_release_date(movie):
            release_date = movie.get('release_date', '')
            if not release_date:
                return datetime.min
            try:
                return datetime.strptime(release_date, '%Y-%m-%d')
            except (ValueError, TypeError):
                return datetime.min

        newest_results = sorted(
            search_results,
            key=get_release_date,
            reverse=True
        )

        # =====================================================
        # HASIL DINAMIS
        # =====================================================

        top_movies = newest_results

        total_movies = len(top_movies)

        print(f"   Total newest movies : {total_movies}")

        # =====================================================
        # EXTRACT DATA
        # =====================================================

        titles = []
        release_dates = []
        vote_averages = []
        vote_counts = []

        for movie in top_movies:

            title = movie.get('title', 'Unknown')

            # Potong judul terlalu panjang
            if len(title) > 35:
                title = title[:35] + '...'

            titles.append(title)

            # Gunakan release_date field
            release_date = movie.get('release_date', 'Unknown')
            release_dates.append(release_date)
            
            vote_averages.append(float(movie.get('vote_average', 0)))
            vote_counts.append(int(movie.get('vote_count', 0)))

        # =====================================================
        # SORT DESCENDING BY RELEASE DATE
        # =====================================================

        combined = list(zip(titles, release_dates, vote_averages, vote_counts))

        combined.sort(
            key=lambda x: x[1] if x[1] != 'Unknown' else '1900-01-01',
            reverse=True
        )

        titles, release_dates, vote_averages, vote_counts = zip(*combined)

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
        # HORIZONTAL BAR CHART
        # =====================================================

        # Hitung hari sejak tanggal rilis terawal untuk panjang bar
        def get_release_date(movie):
            release_date = movie.get('release_date', '')
            if not release_date:
                return datetime.min
            try:
                return datetime.strptime(release_date, '%Y-%m-%d')
            except (ValueError, TypeError):
                return datetime.min

        # Cari tanggal terawal
        dates = [get_release_date(movie) for movie in top_movies]
        earliest_date = min(dates)
        
        # Hitung hari sejak tanggal terawal, tambahkan minimum value agar tidak kosong
        bar_values = [(date - earliest_date).days + 100 for date in dates]
        plot_values = [max(val, 0.01) for val in bar_values]
        
        bar_colors = [
            '#08306b' if i == 0 else
            '#2171b5' if i == 1 else
            '#4292c6' if i == 2 else
            '#9ecae1'
            for i in range(len(bar_values))
        ]

        bars = ax.barh(
            y_pos,
            plot_values,
            color=bar_colors,
            edgecolor='none',
            height=0.62,
            align='center'
        )

        # =====================================================
        # VALUE LABEL (RELEASE DATE)
        # =====================================================

        max_bar_value = max(plot_values) if plot_values else 1
        x_limit = max_bar_value * 1.25 if max_bar_value > 0 else 1

        for i, (date, bar) in enumerate(zip(release_dates, bars)):
            width = bar.get_width()
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
                f"{date}",
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
            f'Hasil Film Terbaru Berdasarkan Query "{query}"',
            fontsize=22,
            fontweight='bold',
            y=0.98
        )

        ax.set_title(
            'Top 20 film terbaru berdasarkan tanggal rilis (log scale)',
            fontsize=12,
            color='#444444',
            pad=24,
            loc='left'
        )

        # =====================================================
        # AXIS LABEL
        # =====================================================

        ax.set_xlabel(
            'Hari Sejak Rilis Terawal [skala log]',
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
        ax.xaxis.set_major_locator(mticker.LogLocator(base=10.0, subs=(1.0,), numticks=6))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))

        # =====================================================
        # INFO BOX
        # =====================================================

        info_text = (
            f"Total Film : {len(titles)}\n"
            "Source : TMDb Dataset\n"
            "Search : TF-IDF + PCC\n"
            "Sorting : Release Date (Newest First)"
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

        png_file = f'newest_tab_{query.replace(" ", "_")}.png'

        pdf_file = f'newest_tab_{query.replace(" ", "_")}.pdf'

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

        print("\n=== HASIL FILM TERBARU ===\n")

        print(
            f"{'Rank':<6}"
            f"{'Title':<40}"
            f"{'Release Date':<15}"
            f"{'Rating':<10}"
            f"{'Votes':<10}"
        )

        print("-" * 100)

        for i, (movie, date) in enumerate(zip(top_movies, release_dates), start=1):

            print(
                f"{i:<6}"
                f"{movie.get('title', 'Unknown')[:40]:<40}"
                f"{date:<15}"
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

    generate_newest_diagram()
