# Hasil Diagram

Folder ini menyimpan diagram tab web untuk 20 film teratas dari seluruh
katalog tanpa filter, serta diagram rekomendasi PCC untuk query pencarian.

| Diagram | PNG | PDF | Urutan |
| --- | --- | --- | --- |
| Populer | `popular_tab_all_movies.png` | `popular_tab_all_movies.pdf` | Rating berbobot, sama dengan tab web |
| Trending | `trending_tab_all_movies.png` | `trending_tab_all_movies.pdf` | Trending Score, sama dengan tab web |
| Terbaru | `newest_tab_all_movies.png` | `newest_tab_all_movies.pdf` | Tanggal rilis terbaru, sama dengan tab web |
| Rekomendasi PCC | `search_pcc_dilan_1990.png` | `search_pcc_dilan_1990.pdf` | Skor PCC tertinggi, dengan Precision@K dan NDCG@K |

Diagram tab memakai katalog dan fungsi filter/pengurutan yang sama dengan
endpoint web `/api/movies`; karena tidak ada filter yang diterapkan, diagram
menampilkan halaman pertama (20 film). Diagram populer menampilkan rating
berbobot yang juga menentukan urutan tab.

Diagram rekomendasi memakai daftar, label kecocokan, skor PCC, dan urutan yang
sama dengan hasil pencarian di web: PCC tertinggi lebih dahulu, lalu
popularitas sebagai pemecah nilai seri. Precision@K, NDCG@K, dan SortCons
dihitung pada daftar itu; film acuan tidak dihitung sebagai rekomendasi.

Untuk memperbarui diagram tab dari root proyek, jalankan:

```powershell
venv\Scripts\python.exe generate_popularity_diagram.py
venv\Scripts\python.exe generate_trending_diagram.py
venv\Scripts\python.exe generate_newest_diagram.py
```

Untuk memperbarui diagram rekomendasi PCC, jalankan generator dari root proyek. Kedua perintah di bawah menggunakan alur pencarian web yang sama dan menaruh PNG serta PDF baru di folder ini.

Diagram hasil pencarian PCC bisa dibuat untuk satu atau beberapa query:

```powershell
venv\Scripts\python.exe generate_search_diagram.py "Dilan 1990"
venv\Scripts\python.exe generate_search_diagram.py "Dilan 1990" "Pengabdi Setan" --top-n 10
venv\Scripts\python.exe generate_pcc_similarity_diagram.py "Dilan 1990"
```

Generator langsung mencetak daftar rekomendasi dengan urutan seperti web, badge kecocokan, status relevansi, dan nilai Precision/NDCG. Tidak perlu mengisi file CSV.

Setiap query menghasilkan file PNG dan PDF sendiri, dengan nama berdasarkan query, misalnya `search_pcc_pengabdi_setan.png`. Jumlah hasil bisa diatur dari 1 sampai 20.

Evaluasi metrik juga bisa dijalankan langsung:

```powershell
venv\Scripts\python.exe precision_ndcg_by_tab.py
```

Evaluator meminta judul acuan yang cocok secara unik dengan dataset, kemudian langsung menampilkan rekomendasi dan menghitung Precision@K serta NDCG@K menggunakan aturan relevansi yang ada di skripsi.
