# STEP 11 — Validation Report

**Generated:** 2026-06-07 · Tolerance: 0.1%

## Overall: ✅ ALL VALIDATIONS PASS

| # | Validation | Result | Detail |
|---|---|---|---|
| | V1 Executive strategic value == SUM(Normalized_Inventory_Value) | ✅ PASS | page0=85,663,636 vs Σnorm=85,663,636 |
| | V2 Procurement page total == SUM(Normalized_Investment_Required) | ✅ PASS | page1=473,115,370 vs policy=473,115,370 |
| | V2b Executive 'Procurement Required' == page1 total | ✅ PASS | page0=473,115,370 vs page1=473,115,370 |
| | V3 Criticality matrix == SUM(Normalized_Inventory_Value) | ✅ PASS | page7=85,663,636 vs Σnorm=85,663,636 |
| | V4 no original value/score columns on strategic pages | ✅ PASS | clean |
| | V5 Top-20 rank comparison generated | ✅ PASS | 2 item(s) moved >10 positions (see step11_top20_rank_comparison.csv) |
| | V6a page5 Inventory_Value == Normalized_Inventory_Value (alias) | ✅ PASS | identical |
| | V6b Description populated on page1/page3/page4/page5 | ✅ PASS | {'page1': 0, 'page3': 0, 'page4': 0, 'page5': 0} |
| | V6c Criticality_Name populated on page1/page3 | ✅ PASS | {'page1': 0, 'page3': 0} |

## V5 — Top 20 Procurement Items: Before vs After Normalization

| Rank Before | Rank After | Δ Rank | PL_Code | Original Value | Normalized Value | >10 |
|---:|---:|---:|---|---:|---:|:--:|
| 1 | 14 | -13 | 56119033 | 52,592,877,381 | 52,592,890 | ⚠️ |
| 2 | 20 | -18 | 56987122/56110029 | 8,800,798,456 | 8,800,796 | ⚠️ |
| 3 | 1 | +2 | 50550081 | 464,269,550 | 464,269,547 |  |
| 4 | 2 | +2 | 56509960 | 458,603,741 | 458,603,695 |  |
| 5 | 3 | +2 | 56501018 | 339,684,638 | 339,684,654 |  |
| 6 | 4 | +2 | 56509959 | 311,663,699 | 311,663,710 |  |
| 7 | 5 | +2 | 56468039 | 309,396,702 | 309,396,571 |  |
| 8 | 6 | +2 | 56468052 | 278,996,169 | 278,996,045 |  |
| 9 | 7 | +2 | 56468040 | 256,356,768 | 256,356,863 |  |
| 10 | 8 | +2 | 50540324 | 250,359,668 | 250,359,722 |  |
| 11 | 9 | +2 | 56501006 | 239,196,656 | 239,196,656 |  |
| 12 | 10 | +2 | 50232356/50232319 | 157,563,948 | 157,564,027 |  |
| 13 | 11 | +2 | 56468027 | 134,913,629 | 134,913,618 |  |
| 14 | 12 | +2 | 56462050 | 98,647,456 | 98,647,273 |  |
| 15 | 13 | +2 | 56119537 | 66,548,075 | 66,548,076 |  |
| 16 | 15 | +1 | 56468064 | 45,812,069 | 45,811,733 |  |
| 17 | 16 | +1 | 50541523 | 31,283,761 | 31,283,708 |  |
| 18 | 17 | +1 | 56451027 | 21,896,391 | 21,896,365 |  |
| 19 | 18 | +1 | 56450217 | 19,312,237 | 19,312,204 |  |
| 20 | 19 | +1 | 52156576/56500452 | 14,686,258 | 14,685,956 |  |