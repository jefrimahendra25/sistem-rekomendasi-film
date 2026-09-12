# TODO - Split Data & Evaluasi Precision/NDCG

- [ ] Terapkan split train/test 80/20 pada evaluasi `precision_evaluation.py` (rekomendasi) dan `precision_search.py` (pencarian).
- [ ] Tambahkan util fungsi split (seed, shuffling, porsi train/test) bila diperlukan.
- [ ] Pastikan perhitungan Precision@K dan NDCG@K tetap sama (menggunakan `is_relevant` dan formula DCG/IDCG seperti sekarang).
- [ ] Tambahkan parameter K (mis. 5,10,20) dan jumlah query (opsional) agar hasil stabil.
- [ ] Jalankan skrip evaluasi untuk verifikasi tidak error.

