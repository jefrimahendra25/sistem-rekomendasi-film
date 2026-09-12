# TODO run plan - NDCG/Precision by tab fix

- [x] Fix missing function call in `precision_ndcg_by_tab.py`: replace `get_tab_ranking_like_web` with a concrete implementation mirroring API sorting/filtering + pagination
- [x] Ensure selected query title is printed clearly after user selection
- [ ] Verify Precision@K and NDCG@K computed for trending/newest/popular using the ranking returned by the corrected function
- [ ] Run quick syntax check / execute script (or run tests if available) to ensure it starts without NameError


