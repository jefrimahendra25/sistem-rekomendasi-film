#!/usr/bin/env python3
"""
Generate PCC Similarity Diagram
Menampilkan diagram hasil perhitungan Pearson Correlation Coefficient (PCC)
untuk similarity antara query dan film-film hasil pencarian
"""

import sys
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer

plt.style.use('ggplot')

# =====================================================
# ADD PROJECT PATH
# =====================================================

sys.path.insert(0, os.path.dirname(__file__))


def generate_pcc_similarity_diagram():

    try:

        print("\n=== GENERATING PCC SIMILARITY DIAGRAM ===\n")

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

        # Gunakan search_movies dari movie_service (sama dengan web)
        search_results = movie_service.search_movies(
            query=query,
            movies=movies,
            min_results=20
        )

        print(f"   Search results found : {len(search_results)}")

        # =====================================================
        # VALIDASI
        # =====================================================

        if not search_results:
            print("\n❌ No movies found")
            return

        # =====================================================
        # CALCULATE TF-IDF + PCC SIMILARITY SCORES (SAMA PERSIS DENGAN BACKEND)
        # =====================================================

        print("\n3. Calculating TF-IDF + PCC similarity scores (same as backend)...")

        query_lower = query.lower()
        query_tokens = movie_service._tokenize_text(query_lower)
        
        import re
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", query_lower)
        query_year = year_match.group(1) if year_match else None

        # Siapkan search documents dengan judul 3x (sama dengan movie_service)
        # Hanya untuk film yang ada di search_results
        processed_movies = []
        search_docs = []
        
        # Buat set dari movie IDs yang ada di search_results
        search_result_ids = set()
        for movie in search_results:
            movie_id = movie.get('id', '')
            if movie_id:
                search_result_ids.add(str(movie_id))
        
        for movie in movies:
            movie_id = movie.get('id', '')
            # Hanya proses film yang ada di search_results
            if str(movie_id) not in search_result_ids:
                continue
                
            title = str(movie.get('title', '')).lower()
            overview = str(movie.get('overview', '')).lower()
            
            # Parsing genres
            genres_list = []
            for genre in movie.get('genres', []):
                if isinstance(genre, dict):
                    genres_list.append(genre.get('name', '').lower())
                else:
                    genres_list.append(str(genre).lower())
            genres_text = ' '.join(genres_list)
            
            # Bobot judul 3x: ulang judul sebanyak 3 kali
            search_doc = f"{title} {title} {title} {overview} {genres_text}"
            
            processed_movies.append({
                'movie': movie,
                'title': title,
                'overview': overview,
                'genres': genres_text,
                'search_doc': search_doc
            })
            search_docs.append(search_doc)

        # Wrapper tokenizer yang mengembalikan list (bukan set)
        def list_tokenizer(text):
            return list(movie_service._tokenize_text(text))

        # TF-IDF Vectorization (sama dengan movie_service)
        stop_words = ['yang', 'di', 'ke', 'dari', 'dan', 'atau', 'dengan', 'untuk', 'pada',
                     'the', 'and', 'of', 'to', 'in', 'a', 'is', 'it', 'that', 'was', 'as', 'on']
        
        vectorizer = TfidfVectorizer(
            tokenizer=list_tokenizer,
            stop_words=stop_words,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.9
        )
        
        try:
            # Fit TF-IDF dengan query + semua search documents
            tfidf_matrix = vectorizer.fit_transform([query_lower] + search_docs)
            dense_matrix = tfidf_matrix.toarray()
            query_vector = dense_matrix[0]
            
            # Hitung similarity untuk setiap film
            similarity_scores = []
            
            for i in range(1, len(dense_matrix)):
                doc_vector = dense_matrix[i]
                
                # Hitung Pearson Correlation Coefficient
                if np.std(query_vector) == 0 or np.std(doc_vector) == 0:
                    pcc = 0.0
                else:
                    pcc, _ = stats.pearsonr(query_vector, doc_vector)
                    pcc = (pcc + 1) / 2  # Convert dari [-1, 1] ke [0, 1]
                
                similarity_scores.append(max(0.0, min(1.0, pcc)))
            
            print(f"   TF-IDF + PCC calculation successful")
            print(f"   Query vector shape: {query_vector.shape}")
                
        except Exception as e:
            print(f"   Error in TF-IDF/PCC calculation: {e}")
            import traceback
            traceback.print_exc()
            similarity_scores = [0.0] * len(processed_movies)

        # =====================================================
        # CALCULATE FINAL SCORES (SAMA PERSIS DENGAN BACKEND)
        # =====================================================

        print("\n4. Calculating final scores with validation (same as backend)...")

        scored_movies = []
        
        for idx, score in enumerate(similarity_scores):
            if idx >= len(processed_movies):
                continue
            
            movie_data = processed_movies[idx]
            movie = movie_data['movie']
            title = movie_data['title']
            overview = movie_data['overview']
            genres_text = movie_data['genres']
            
            title_tokens = movie_service._tokenize_text(title)
            overview_tokens = movie_service._tokenize_text(overview)
            genre_tokens = movie_service._tokenize_text(genres_text)
            
            has_title_overlap = bool(query_tokens.intersection(title_tokens))
            has_overview_overlap = bool(query_tokens.intersection(overview_tokens))
            has_genre_overlap = bool(query_tokens.intersection(genre_tokens))
            query_title_sim = movie_service._title_similarity(query_lower, title)
            query_overview_sim = movie_service._calculate_string_similarity(query_lower, overview)
            phrase_in_title = movie_service._phrase_match(query_lower, title)
            phrase_in_overview = movie_service._phrase_match(query_lower, overview)
            query_substring_in_title = any(tok in title for tok in query_tokens)
            query_substring_in_overview = any(tok in overview for tok in query_tokens)
            
            # Filtering logic (sama dengan backend)
            if not (has_title_overlap or has_overview_overlap or has_genre_overlap or query_substring_in_title or query_substring_in_overview):
                if score < 0.75 and query_title_sim < 0.25:
                    continue
            elif has_genre_overlap and not (has_title_overlap or has_overview_overlap or query_substring_in_title or query_substring_in_overview):
                if score < 0.70:
                    continue
            
            # Title score calculation
            title_score = 0.0
            if has_title_overlap:
                overlap_ratio = len(query_tokens.intersection(title_tokens)) / max(len(query_tokens), 1)
                title_score = 0.30 + overlap_ratio * 0.20
            elif query_substring_in_title:
                title_score = 0.22 + query_title_sim * 0.20
            else:
                title_score = query_title_sim * 0.18
            
            # Overview score calculation
            overview_score = 0.0
            if has_overview_overlap:
                overlap_ratio = len(query_tokens.intersection(overview_tokens)) / max(len(query_tokens), 1)
                overview_score = 0.18 + overlap_ratio * 0.18
            elif query_substring_in_overview:
                overview_score = 0.12 + query_overview_sim * 0.15
            else:
                overview_score = query_overview_sim * 0.10
            
            # Genre score calculation
            genre_score = (len(query_tokens.intersection(genre_tokens)) / max(len(query_tokens), 1)) * 0.15
            
            # Final score calculation
            final_score = (score * 0.30) + title_score + overview_score + genre_score
            
            # Bonus scores
            if phrase_in_title:
                final_score += 0.05
            if phrase_in_overview:
                final_score += 0.03
            if query_year and str(movie.get('release_date', '')).startswith(query_year):
                final_score += 0.10
            if {'dilan', 'milea'}.intersection(query_tokens):
                if 'dilan' in title or 'milea' in title or 'dilan' in overview or 'milea' in overview:
                    final_score += 0.08
            
            final_score = min(1.0, final_score)
            
            if final_score < 0.12:
                continue
            
            scored_movies.append({
                'movie': movie,
                'similarity_score': final_score
            })

        # Sort by similarity score descending
        scored_movies.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Get top 20
        top_movies = scored_movies[:20]

        print(f"   Total movies with final scores : {len(scored_movies)}")
        print(f"   Top 20 movies selected")

        # =====================================================
        # EXTRACT DATA FOR DIAGRAM
        # =====================================================

        titles = []
        scores = []

        for item in top_movies:
            movie = item['movie']
            title = movie.get('title', 'Unknown')
            
            # Potong judul terlalu panjang
            if len(title) > 35:
                title = title[:35] + '...'
            
            titles.append(title)
            scores.append(item['similarity_score'])

        # =====================================================
        # FIGURE SIZE
        # =====================================================

        fig_height = max(10, len(titles) * 0.35)

        fig, ax = plt.subplots(
            figsize=(16, fig_height)
        )
        fig.subplots_adjust(left=0.38, right=0.95, top=0.86, bottom=0.20)

        # =====================================================
        # HORIZONTAL BAR CHART
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

        max_score = max(scores) if scores else 1
        x_limit = max_score * 1.15 if max_score > 0 else 1

        for i, (score, bar) in enumerate(zip(scores, bars)):
            width = bar.get_width()
            if score > 0:
                label_x = width + 0.02
                ha = 'left'
                label_color = '#222222'
            else:
                label_x = 0.01
                ha = 'left'
                label_color = '#888888'

            if label_x >= x_limit:
                label_x = width - 0.02
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
        ax.xaxis.set_major_locator(mticker.MultipleLocator(0.1))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))

        ax.set_xlabel(
            'PCC Similarity Score [0-1]',
            fontsize=13,
            fontweight='bold'
        )
        ax.set_ylabel(
            'Judul Film',
            fontsize=13,
            fontweight='bold'
        )

        fig.suptitle(
            f'Hasil Pencarian TF-IDF + PCC untuk Query "{query}"',
            fontsize=22,
            fontweight='bold',
            y=0.98
        )

        ax.set_title(
            'Top 20 film berdasarkan ranking TF-IDF + PCC',
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
            "Method : TF-IDF + PCC\n"
            "Similarity : Pearson Correlation Coefficient"
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
        # OUTPUT FILE
        # =====================================================

        png_file = f'pcc_similarity_{query.replace(" ", "_")}.png'
        pdf_file = f'pcc_similarity_{query.replace(" ", "_")}.pdf'

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

        print("\n=== HASIL PENCARIAN TF-IDF + PCC ===\n")

        print(
            f"{'Rank':<6}"
            f"{'Title':<40}"
            f"{'Similarity':<12}"
            f"{'Rating':<10}"
        )

        print("-" * 90)

        for i, item in enumerate(top_movies, start=1):
            movie = item['movie']
            print(
                f"{i:<6}"
                f"{movie.get('title', 'Unknown')[:40]:<40}"
                f"{item['similarity_score']:<12.2f}"
                f"{movie.get('vote_average', 0):<10.1f}"
            )

        print("\n✅ PCC Similarity diagram generation completed successfully!\n")

    except Exception as e:

        print(f"\n❌ ERROR : {e}")

        import traceback
        traceback.print_exc()


# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':

    generate_pcc_similarity_diagram()
