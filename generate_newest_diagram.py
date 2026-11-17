#!/usr/bin/env python3
"""Generate a diagram of the web's Newest tab."""

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
        # Match /api/movies?type=newest: filter, sort, then take page one.
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

        newest_results = movie_service.sort_movies(filtered_movies, 'newest')

        # =====================================================
        # HASIL DINAMIS
        # =====================================================

        top_movies = newest_results[:20]

        total_movies = len(top_movies)

        print(f"   Total newest movies : {total_movies}")

        # =====================================================
        # EXTRACT DATA
        # =====================================================

        titles = []
        release_dates = []
        vote_averages = []
        vote_counts = []
        parsed_dates = []

        for movie in top_movies:
            title = movie.get('title', 'Unknown')
            if len(title) > 35:
                title = title[:35] + '...'
            titles.append(title)

            release_date = movie.get('release_date', '')
            release_dates.append(release_date or 'Unknown')
            parsed_dates.append(get_release_date(movie))

            try:
                vote_averages.append(float(movie.get('vote_average') or 0))
            except (TypeError, ValueError):
                vote_averages.append(0.0)
            try:
                vote_counts.append(int(float(movie.get('vote_count') or 0)))
            except (TypeError, ValueError):
                vote_counts.append(0)

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
        # HORIZONTAL BAR CHART
        # =====================================================

        valid_dates = [date for date in parsed_dates if date != datetime.min]
        earliest_date = min(valid_dates) if valid_dates else None
        bar_values = [
            (date - earliest_date).days if earliest_date and date != datetime.min else 0
            for date in parsed_dates
        ]
        max_bar_value = max(bar_values, default=0)
        x_limit = max_bar_value * 1.2 if max_bar_value else 1
        
        bar_colors = [
            '#08306b' if i == 0 else
            '#2171b5' if i == 1 else
            '#4292c6' if i == 2 else
            '#9ecae1'
            for i in range(len(bar_values))
        ]

        bars = ax.barh(
            y_pos,
            bar_values,
            color=bar_colors,
            edgecolor='none',
            height=0.62,
            align='center'
        )

        # =====================================================
        # VALUE LABEL (RELEASE DATE)
        # =====================================================

        for i, (date, bar) in enumerate(zip(release_dates, bars)):
            width = bar.get_width()
            label_x = max(width * 1.02, max_bar_value * 0.01)
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
        ax.set_xlim(0, x_limit)

        # =====================================================
        # TITLE
        # =====================================================

        fig.suptitle(
            'Hasil Film Terbaru pada Tab Web',
            fontsize=22,
            fontweight='bold',
            y=0.98
        )

        ax.set_title(
            '20 film teratas berdasarkan tanggal rilis terbaru',
            fontsize=12,
            color='#444444',
            pad=24,
            loc='left'
        )

        # =====================================================
        # AXIS LABEL
        # =====================================================

        ax.set_xlabel(
            'Hari sejak tanggal rilis terawal',
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
        ax.xaxis.set_major_locator(mticker.MaxNLocator(6, integer=True))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))

        # =====================================================
        # INFO BOX
        # =====================================================

        info_text = (
            f"Total Film : {len(titles)}\n"
            "Sumber : Katalog film web\n"
            "Filter : Semua genre dan tahun\n"
            "Urutan : Tanggal rilis terbaru"
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
        png_file = os.path.join(output_dir, 'newest_tab_all_movies.png')
        pdf_file = os.path.join(output_dir, 'newest_tab_all_movies.pdf')

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
