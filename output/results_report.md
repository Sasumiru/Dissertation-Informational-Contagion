# Results report

Main spec: 107 banks, logistic mapping, s0 = 0.6508, tau = 0.9442 (90th pct), strong-link cut-off = 0.8393 (75th pct, 1418 links), delta = 0.5.

## Validation

| Check | Result | Numbers |
|---|---|---|
| Similarity matrix symmetric, diagonal 0 | PASS | max asymmetry 0.0e+00, max diagonal 0.0e+00, all 37 runs |
| direct + indirect = total | PASS | 0 mismatches across 37 runs |
| Sum of exposure = sum of total reach | PASS | main: 6433 = 6433, 0 runs differ |
| No trigger distresses itself | PASS | 0 cases in cascade_rounds_main.csv (multiround asserts this for every run too) |
| Direct reach same across logistic, linear, convex (and = single-round total) | PASS | 0 mismatches |
| Recomputed centrality = _thresh columns in network_metrics.csv | PASS | max difference 7.1e-15 |
| Four public-sector banks found | PASS | BNG Bank N.V.; SFIL S.A.; Kommuninvest - Grupp; Kuntarahoitus Oyj |

## Descriptive statistics

| Measure | Mean | Median | Min | Max | Std dev | Zeros |
|---|---|---|---|---|---|---|
| total_reach | 60.12 | 81 | 0 | 94 | 37.25 | 23 |
| direct_reach | 10.62 | 9 | 0 | 29 | 9.72 | 23 |
| indirect_reach | 49.50 | 60 | 0 | 92 | 31.77 | 28 |
| exposure | 60.12 | 70 | 0 | 79 | 24.92 | 4 |
| rounds | 3.97 | 4 | 0 | 8 | 2.52 | 23 |

## Rankings

23 of 107 triggers have total reach 0, 28 have indirect reach 0. rho(total reach, exposure) = 0.79 (p <0.001). Ranks are average ranks, ties with 10th kept.

**Top 10 by total reach**

| Rank | Bank | Country | Total | Direct | Indirect | Rounds |
|---|---|---|---|---|---|---|
| 1 | Groupe Crédit Agricole | FR | 94 | 2 | 92 | 4 |
| 4 | Abanca Corporacion Bancaria, S.A. | ES | 92 | 9 | 83 | 4 |
| 4 | Banco de Sabadell, S.A. | ES | 92 | 8 | 84 | 4 |
| 4 | CaixaBank, S.A. | ES | 92 | 4 | 88 | 4 |
| 4 | LSF NANI INVESTMENTS S.A R.L. | PT | 92 | 15 | 77 | 4 |
| 4 | MBH bankcsoport | HU | 92 | 14 | 78 | 4 |
| 8 | Bankinter, S.A. | ES | 91 | 13 | 78 | 4 |
| 8 | ING Groep N.V. | NL | 91 | 8 | 83 | 4 |
| 8 | KBC Groupe | BE | 91 | 13 | 78 | 4 |
| 15.5 | Akcinė bendrovė Šiaulių bankas | LT | 90 | 4 | 86 | 5 |
| 15.5 | BANCA POPOLARE DI SONDRIO SOCIETA' PER AZIONI | IT | 90 | 24 | 66 | 4 |
| 15.5 | BNP Paribas | FR | 90 | 22 | 68 | 4 |
| 15.5 | BPER Banca S.p.A. | IT | 90 | 13 | 77 | 5 |
| 15.5 | Banco Bilbao Vizcaya Argentaria, S.A. | ES | 90 | 15 | 75 | 5 |
| 15.5 | Banco Comercial Português, SA | PT | 90 | 21 | 69 | 4 |
| 15.5 | Bank Polska Kasa Opieki S.A. | PL | 90 | 24 | 66 | 4 |
| 15.5 | Caixa Geral de Depósitos, S.A. | PT | 90 | 15 | 75 | 4 |
| 15.5 | Intesa Sanpaolo S.p.A. | IT | 90 | 16 | 74 | 5 |
| 15.5 | OTP-csoport | HU | 90 | 22 | 68 | 4 |
| 15.5 | Powszechna Kasa Oszczednosci Bank Polski S.A. | PL | 90 | 18 | 72 | 5 |
| 15.5 | UNICREDIT, SOCIETA' PER AZIONI | IT | 90 | 19 | 71 | 4 |

**Bottom 10 by total reach**

| Rank | Bank | Country | Total | Direct | Indirect | Rounds |
|---|---|---|---|---|---|---|
| 96 | ABN AMRO Bank N.V. | NL | 0 | 0 | 0 | 0 |
| 96 | AIB Group plc | IE | 0 | 0 | 0 | 0 |
| 96 | Banca Transilvania | RO | 0 | 0 | 0 | 0 |
| 96 | Belfius Bank | BE | 0 | 0 | 0 | 0 |
| 96 | CEC BANK SA | RO | 0 | 0 | 0 | 0 |
| 96 | Coöperatieve Rabobank U.A.2 | NL | 0 | 0 | 0 | 0 |
| 96 | Crelan | BE | 0 | 0 | 0 | 0 |
| 96 | DEUTSCHE BANK AKTIENGESELLSCHAFT | DE | 0 | 0 | 0 | 0 |
| 96 | FINECOBANK S.P.A. | IT | 0 | 0 | 0 | 0 |
| 96 | HSBC Continental Europe | FR | 0 | 0 | 0 | 0 |
| 96 | Hamburg Commercial Bank AG | DE | 0 | 0 | 0 | 0 |
| 96 | Investeringsmaatschappij Argenta | BE | 0 | 0 | 0 | 0 |
| 96 | Kutxabank, S.A. | ES | 0 | 0 | 0 | 0 |
| 96 | MDB Group Limited | MT | 0 | 0 | 0 | 0 |
| 96 | Mediobanca - Banca di Credito Finanziario S.p.A. | IT | 0 | 0 | 0 | 0 |
| 96 | Morgan Stanley Europe Holding SE | DE | 0 | 0 | 0 | 0 |
| 96 | RBS Holdings N.V. | NL | 0 | 0 | 0 | 0 |
| 96 | SFIL S.A. | FR | 0 | 0 | 0 | 0 |
| 96 | Société générale S.A. | FR | 0 | 0 | 0 | 0 |
| 96 | State Street Europe Holdings Germany S.a.r.l. & Co. KG | DE | 0 | 0 | 0 | 0 |
| 96 | UBS Europe SE | DE | 0 | 0 | 0 | 0 |
| 96 | Unicaja Banco, S.A. | ES | 0 | 0 | 0 | 0 |
| 96 | de Volksbank N.V. | NL | 0 | 0 | 0 | 0 |

**Top 10 by exposure**

| Rank | Bank | Country | Exposure |
|---|---|---|---|
| 1 | AIB Group plc | IE | 79 |
| 11.5 | AIKGROUP (CY) LIMITED | SI | 78 |
| 11.5 | Abanca Corporacion Bancaria, S.A. | ES | 78 |
| 11.5 | Akciju sabiedrība "Citadele banka" | LV | 78 |
| 11.5 | Akcinė bendrovė Šiaulių bankas | LT | 78 |
| 11.5 | BANCA POPOLARE DI SONDRIO SOCIETA' PER AZIONI | IT | 78 |
| 11.5 | BNP Paribas | FR | 78 |
| 11.5 | Banco Santander, S.A. | ES | 78 |
| 11.5 | Banco de Sabadell, S.A. | ES | 78 |
| 11.5 | Bankinter, S.A. | ES | 78 |
| 11.5 | Bpifrance | FR | 78 |
| 11.5 | Caixa Geral de Depósitos, S.A. | PT | 78 |
| 11.5 | DNB BANK ASA | NO | 78 |
| 11.5 | Groupe Crédit Agricole | FR | 78 |
| 11.5 | ING Groep N.V. | NL | 78 |
| 11.5 | KBC Groupe | BE | 78 |
| 11.5 | LSF NANI INVESTMENTS S.A R.L. | PT | 78 |
| 11.5 | MBH bankcsoport | HU | 78 |
| 11.5 | Raiffeisen Bank International AG | AT | 78 |
| 11.5 | Raiffeisenbankengruppe OÖ Verbund eGen | AT | 78 |
| 11.5 | UNICREDIT, SOCIETA' PER AZIONI | IT | 78 |

**Bottom 10 by exposure**

| Rank | Bank | Country | Exposure |
|---|---|---|---|
| 105.5 | FINECOBANK S.P.A. | IT | 0 |
| 105.5 | SFIL S.A. | FR | 0 |
| 105.5 | State Street Europe Holdings Germany S.a.r.l. & Co. KG | DE | 0 |
| 105.5 | de Volksbank N.V. | NL | 0 |
| 101.5 | LGT Group Foundation | LI | 1 |
| 101.5 | RCI Banque | FR | 1 |
| 101.5 | Revolut Holdings Europe UAB | LT | 1 |
| 101.5 | Volkswagen Financial Services AG | DE | 1 |
| 99 | Coöperatieve Rabobank U.A.2 | NL | 3 |
| 98 | ABN AMRO Bank N.V. | NL | 5 |

## Mapping and rounds comparison

Spearman rho between the main ranking and each alternative, top-10 overlap counts ties.

| Comparison | Measure | rho | p-value | Top-10 overlap |
|---|---|---|---|---|
| linear | direct_reach | 1.00 | <0.001 | 12/12 |
| linear | indirect_reach | 0.89 | <0.001 | 8/11 |
| linear | total_reach | 0.94 | <0.001 | 13/21 |
| linear | exposure | 0.74 | <0.001 | 21/21 |
| convex | direct_reach | 1.00 | <0.001 | 12/12 |
| convex | indirect_reach | 0.99 | <0.001 | 10/11 |
| convex | total_reach | 0.99 | <0.001 | 18/21 |
| convex | exposure | 0.97 | <0.001 | 16/21 |
| single | total_reach | 0.58 | <0.001 | 0/21 |
| single | exposure | 0.36 | <0.001 | 0/21 |

## Centrality and indirect reach

Strong-link network. Partial rho controls for log_total_assets, cet1_ratio, direct_reach.

| Centrality | rho | p-value | Partial rho | Partial p-value |
|---|---|---|---|---|
| Weighted degree | 0.57 | <0.001 | 0.48 | <0.001 |
| Eigenvector | 0.46 | <0.001 | 0.33 | 0.001 |
| PageRank | 0.67 | <0.001 | 0.58 | <0.001 |
| Betweenness | 0.43 | <0.001 | 0.26 | 0.008 |

## Robustness

Each run changes one setting from the main spec. complete_centrality only changes the centrality network.

| Run | Mean total reach | Zero reach | rho(reach, exposure) | Total reach rho vs main | Partial rho Weighted degree | Partial rho Eigenvector | Partial rho PageRank | Partial rho Betweenness |
|---|---|---|---|---|---|---|---|---|
| main | 60.12 | 23 | 0.79 | - | 0.48 | 0.33 | 0.58 | 0.26 |
| no_public_banks | 59.19 | 20 | 0.77 | 0.97 | 0.51 | 0.34 | 0.53 | 0.23 |
| strong_link_70 | 69.28 | 23 | 0.47 | 0.92 | 0.43 | 0.27 | 0.53 | 0.32 |
| strong_link_80 | 51.22 | 23 | 0.87 | 0.97 | 0.31 | 0.29 | 0.34 | 0.35 |
| complete_centrality | 60.12 | 23 | 0.79 | - | 0.74 | 0.73 | 0.74 | 0.37 |
| delta_1.0 | 71.63 | 23 | -0.12 | 0.89 | 0.25 | 0.23 | 0.31 | 0.13 |
| delta_0.3 | 41.71 | 23 | 0.82 | 0.92 | 0.44 | 0.33 | 0.50 | 0.27 |
| delta_0.7 | 67.79 | 23 | 0.14 | 0.92 | 0.26 | 0.21 | 0.35 | 0.17 |
| tau_95 | 48.92 | 38 | 0.54 | 0.75 | 0.58 | 0.21 | 0.68 | 0.28 |
| later_rounds_full | 79.50 | 23 | -0.61 | 0.83 | 0.13 | 0.11 | 0.29 | 0.11 |

## Extra checks

| Check | Value | Detail |
|---|---|---|
| zero_reach_equals_no_lookalike | 1.0000 | 23 zero reach banks, 23 with no match above similarity 0.9336, 23 in both |
| median_similarity_with_real_estate | 0.6508 | should match s0 in run_parameters.csv |
| median_similarity_without_real_estate | 0.6836 | real estate dropped, shares re-normalised |
| real_estate_share_min | 0.0060 |  |
| real_estate_share_max | 0.9754 |  |
| cascading_rho_direct_vs_indirect | -0.2895 | n = 84, p 0.008 |
| cascading_partial_weighted_degree | 0.5155 | n = 84, p <0.001 |
| cascading_partial_eigenvector | 0.3229 | n = 84, p 0.003 |
| cascading_partial_pagerank | 0.5447 | n = 84, p <0.001 |
| cascading_partial_betweenness | 0.3223 | n = 84, p 0.003 |
| h1_all_mean_similarity_vs_total_reach | 0.7896 | n = 107, p <0.001 |
| h1_all_n_strong_links_vs_total_reach | 0.7367 | n = 107, p <0.001 |
| h1_all_max_similarity_vs_total_reach | 0.4500 | n = 107, p <0.001 |
| h1_cascading_mean_similarity_vs_total_reach | 0.8452 | n = 84, p <0.001 |
| h1_cascading_n_strong_links_vs_total_reach | 0.5246 | n = 84, p <0.001 |
| h1_cascading_max_similarity_vs_total_reach | -0.1227 | n = 84, p 0.266 |
| spectral_radius_f_strong | 33.4726 | f(s) on 1418 strong links, zero diagonal |
