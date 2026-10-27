# Results report

## 1. Run summary

- Date: 2026-10-27
- Git commit (code): `4cfb96d6b6e82e5f9db38aa7bc6f2ddc5603ae6a` on branch `final-analysis` (WARNING: uncommitted changes in codebase/)
- Number of banks: 107 (pairs: 5671)
- Mapping: logistic, f(s) = 1 / (1 + exp(-10(s - s0))); robustness linear 0.5*s and convex s^2
- s0 (median off-diagonal similarity) = 0.6508
- Distress threshold: tau = 90th percentile of off-diagonal f(s) = 0.9442
- Strong links: similarity >= 75th percentile = 0.8393, giving 1418 strong links
- Decay delta = 0.5; later rounds along strong links
- Centrality: strong-link network (`_thresh` columns of network_metrics.csv)
- Partial-correlation controls: log_total_assets, cet1_ratio, direct_reach
- Run as: `python codebase/multiround.py` then `python codebase/analysis.py`

| Main-spec variant | tau | s0 | Strong cut-off | Strong links |
|---|---|---|---|---|
| Linear mapping | 0.4668 | 0.6508 | 0.8393 | 1418 |
| Convex mapping | 0.8715 | 0.6508 | 0.8393 | 1418 |

## 2. Validation checks

| Check | Result | Numbers |
|---|---|---|
| 1. Similarity matrix symmetric, diagonal 0 | PASS | max abs(S - S transposed) = 0.0e+00, max abs(diagonal) = 0.0e+00 (all 37 runs) |
| 2. direct + indirect = total for every trigger | PASS | 0 mismatches across 37 runs x every trigger |
| 3. Sum of exposure = sum of total_reach | PASS | main: 6433 = 6433; 0 of 37 runs differ |
| 4. No trigger counts itself as distressed | PASS | 0 self-distress cases across 37 runs x 107 triggers |
| 5a. Deterministic: in-memory rerun identical to saved CSVs | PASS | 39 files compared character for character, 0 differ |
| 5b. Deterministic: both scripts rerun from scratch, outputs byte-identical | see note | done outside the scripts, hashes in output/determinism_check.txt |
| 6a. Reference: delta=1.0, tau=90th, later rounds on full network | PASS | 76.6% distress all 106 (ref ~77%), 21.5% distress none (ref ~21%) |
| 6b. Reference: main spec | PASS | 21.5% distress none (ref ~21%), mean total_reach = 60.12 (ref ~60) |
| 7. direct_reach identical across logistic, linear, convex (and = single-round total) | PASS | 0 mismatching triggers across 9 runs |
| 8. Recomputed strong-link centrality = _thresh columns in network_metrics.csv | PASS | max abs difference = 7.1e-15 |
| 9. Exactly 4 public-sector banks matched by name | PASS | BNG Bank N.V.; SFIL S.A.; Kommuninvest - Grupp; Kuntarahoitus Oyj |

## 3. Descriptive statistics (main spec)

| Measure | Mean | Median | Min | Max | Std dev | Zeros |
|---|---|---|---|---|---|---|
| total_reach | 60.12 | 81 | 0 | 94 | 37.25 | 23 |
| direct_reach | 10.62 | 9 | 0 | 29 | 9.72 | 23 |
| indirect_reach | 49.50 | 60 | 0 | 92 | 31.77 | 28 |
| exposure | 60.12 | 70 | 0 | 79 | 24.92 | 4 |
| rounds | 3.97 | 4 | 0 | 8 | 2.52 | 23 |

## 4. RQ1: Rankings

Triggers with total reach = 0: **23** of 107. Triggers with indirect reach = 0: **28**. Spearman rho(total reach, exposure) = **0.79** (p <0.001).

Ranks are average ranks, 1 = highest. Banks tied with the 10th are included.

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

## 5. RQ2: Robustness of the rankings (main spec)

Spearman rho between the main-spec ranking and the alternative. The top-10 overlap is the number of main-spec top-10 banks (ties included) that are also in the alternative's top 10.

| Comparison | Measure | rho | p-value | Top-10 overlap |
|---|---|---|---|---|
| Linear mapping | Direct reach | 1.00 | <0.001 | 12/12 |
| Linear mapping | Indirect reach | 0.89 | <0.001 | 8/11 |
| Linear mapping | Total reach | 0.94 | <0.001 | 13/21 |
| Linear mapping | Exposure | 0.74 | <0.001 | 21/21 |
| Convex mapping | Direct reach | 1.00 | <0.001 | 12/12 |
| Convex mapping | Indirect reach | 0.99 | <0.001 | 10/11 |
| Convex mapping | Total reach | 0.99 | <0.001 | 18/21 |
| Convex mapping | Exposure | 0.97 | <0.001 | 16/21 |
| Single-round model | Total reach | 0.58 | <0.001 | 0/21 |
| Single-round model | Exposure | 0.36 | <0.001 | 0/21 |

## 6. RQ3: Centrality and indirect reach (main spec, strong-link network)

Partial Spearman controls: log(total assets), CET1 ratio, direct reach. n = 107, df for the partial test = 102.

| Centrality | Spearman rho | p-value | Partial rho | Partial p-value | pingouin check |
|---|---|---|---|---|---|
| Weighted degree | 0.57 | <0.001 | 0.48 | <0.001 | not available (pingouin not installed) |
| Eigenvector | 0.46 | <0.001 | 0.33 | 0.001 | not available (pingouin not installed) |
| PageRank | 0.67 | <0.001 | 0.58 | <0.001 | not available (pingouin not installed) |
| Betweenness | 0.43 | <0.001 | 0.26 | 0.008 | not available (pingouin not installed) |

## 7. Robustness

Each run changes one setting from the main spec. Cells show Spearman rho (p-value), plus the top-10 overlap where relevant. For RQ2 rows, the comparison is inside the same run: that run's logistic multi-round ranking against its own linear, convex or single-round version.

### Without the four public-sector banks (`no_public_banks`)

Values used: n = 103 banks, s0 = 0.6624, tau = 0.9371, strong-link cut-off = 0.8410, strong links = 1314; delta = 0.5, tau percentile = 90, strong-link percentile = 75, later rounds = strong, centrality = strong network (recomputed).

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 59.19 |
| RQ1 | Triggers with total reach = 0 | 23 | 20 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 25 |
| RQ1 | rho(total reach, exposure) | 0.79 | 0.77 |
| RQ1 | Total reach vs main spec | - | 0.97 (p <0.001), top-10 16/21 |
| RQ1 | Exposure vs main spec | - | 0.98 (p <0.001), top-10 17/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.93 (p <0.001), top-10 11/16 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.74 (p <0.001), top-10 17/17 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 0.99 (p <0.001), top-10 15/16 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 0.99 (p <0.001), top-10 16/17 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.60 (p <0.001), top-10 1/16 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | 0.38 (p <0.001), top-10 0/17 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 0.83 (p <0.001), top-10 8/10 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 0.99 (p <0.001), top-10 10/10 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.60 (p <0.001); partial 0.51 (p <0.001) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.47 (p <0.001); partial 0.34 (p <0.001) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.64 (p <0.001); partial 0.53 (p <0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.41 (p <0.001); partial 0.23 (p 0.024) |

**Headline vs main spec:** RQ1 unchanged; RQ2 unchanged; RQ3 (partial rho) Weighted degree unchanged, Eigenvector unchanged, PageRank unchanged, Betweenness unchanged.

### Strong-link cut-off at the 70th percentile (`strong_link_70`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9442, strong-link cut-off = 0.8053, strong links = 1702; delta = 0.5, tau percentile = 90, strong-link percentile = 70, later rounds = strong, centrality = strong network (recomputed).

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 69.28 |
| RQ1 | Triggers with total reach = 0 | 23 | 23 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 26 |
| RQ1 | rho(total reach, exposure) | 0.79 | 0.47 |
| RQ1 | Total reach vs main spec | - | 0.92 (p <0.001), top-10 10/21 |
| RQ1 | Exposure vs main spec | - | 0.61 (p <0.001), top-10 17/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.96 (p <0.001), top-10 11/13 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.91 (p <0.001), top-10 46/46 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 0.98 (p <0.001), top-10 10/13 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 0.95 (p <0.001), top-10 10/46 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.46 (p <0.001), top-10 0/13 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | 0.09 (p 0.346), top-10 0/46 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 0.99 (p <0.001), top-10 11/11 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 0.99 (p <0.001), top-10 11/11 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.45 (p <0.001); partial 0.43 (p <0.001) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.28 (p 0.003); partial 0.27 (p 0.005) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.55 (p <0.001); partial 0.53 (p <0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.38 (p <0.001); partial 0.32 (p 0.001) |

**Headline vs main spec:** RQ1 weaker; RQ2 weaker; RQ3 (partial rho) Weighted degree weaker, Eigenvector weaker, PageRank unchanged, Betweenness stronger.

### Strong-link cut-off at the 80th percentile (`strong_link_80`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9442, strong-link cut-off = 0.8757, strong links = 1135; delta = 0.5, tau percentile = 90, strong-link percentile = 80, later rounds = strong, centrality = strong network (recomputed).

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 51.22 |
| RQ1 | Triggers with total reach = 0 | 23 | 23 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 29 |
| RQ1 | rho(total reach, exposure) | 0.79 | 0.87 |
| RQ1 | Total reach vs main spec | - | 0.97 (p <0.001), top-10 10/21 |
| RQ1 | Exposure vs main spec | - | 0.83 (p <0.001), top-10 15/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.98 (p <0.001), top-10 10/11 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.82 (p <0.001), top-10 16/17 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 0.99 (p <0.001), top-10 11/11 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 0.91 (p <0.001), top-10 11/17 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.58 (p <0.001), top-10 0/11 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | 0.58 (p <0.001), top-10 0/17 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 0.97 (p <0.001), top-10 11/11 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 0.99 (p <0.001), top-10 10/11 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.52 (p <0.001); partial 0.31 (p 0.002) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.47 (p <0.001); partial 0.29 (p 0.003) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.57 (p <0.001); partial 0.34 (p <0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.53 (p <0.001); partial 0.35 (p <0.001) |

**Headline vs main spec:** RQ1 stronger; RQ2 unchanged; RQ3 (partial rho) Weighted degree weaker, Eigenvector unchanged, PageRank weaker, Betweenness stronger.

### Centrality on the complete network (RQ3 only) (`complete_centrality`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9442, strong-link cut-off = 0.8393, strong links = 1418; delta = 0.5, tau percentile = 90, strong-link percentile = 75, later rounds = strong, centrality = complete network.

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.78 (p <0.001); partial 0.74 (p <0.001) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.78 (p <0.001); partial 0.73 (p <0.001) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.78 (p <0.001); partial 0.74 (p <0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.52 (p <0.001); partial 0.37 (p <0.001) |

**Headline vs main spec:** RQ1 n/a (cascade identical to main spec); RQ2 n/a (cascade identical to main spec); RQ3 (partial rho) Weighted degree stronger, Eigenvector stronger, PageRank stronger, Betweenness stronger.

### No decay (delta = 1.0) (`delta_1.0`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9442, strong-link cut-off = 0.8393, strong links = 1418; delta = 1.0, tau percentile = 90, strong-link percentile = 75, later rounds = strong, centrality = strong network.

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 71.63 |
| RQ1 | Triggers with total reach = 0 | 23 | 23 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 28 |
| RQ1 | rho(total reach, exposure) | 0.79 | -0.12 |
| RQ1 | Total reach vs main spec | - | 0.89 (p <0.001), top-10 18/21 |
| RQ1 | Exposure vs main spec | - | 0.19 (p 0.047), top-10 1/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.84 (p <0.001), top-10 28/28 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.85 (p <0.001), top-10 15/15 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 1.00 (p <0.001), top-10 28/28 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 0.94 (p <0.001), top-10 14/15 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.46 (p <0.001), top-10 0/28 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | -0.13 (p 0.194), top-10 0/15 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 1.00 (p <0.001), top-10 14/17 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 1.00 (p <0.001), top-10 17/17 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.30 (p 0.002); partial 0.25 (p 0.012) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.26 (p 0.007); partial 0.23 (p 0.020) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.39 (p <0.001); partial 0.31 (p 0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.22 (p 0.024); partial 0.13 (p 0.202) |

**Headline vs main spec:** RQ1 reversed; RQ2 weaker; RQ3 (partial rho) Weighted degree weaker, Eigenvector weaker, PageRank weaker, Betweenness weaker.

### Decay delta = 0.3 (`delta_0.3`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9442, strong-link cut-off = 0.8393, strong links = 1418; delta = 0.3, tau percentile = 90, strong-link percentile = 75, later rounds = strong, centrality = strong network.

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 41.71 |
| RQ1 | Triggers with total reach = 0 | 23 | 23 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 28 |
| RQ1 | rho(total reach, exposure) | 0.79 | 0.82 |
| RQ1 | Total reach vs main spec | - | 0.92 (p <0.001), top-10 4/21 |
| RQ1 | Exposure vs main spec | - | 0.88 (p <0.001), top-10 8/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.98 (p <0.001), top-10 4/12 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.95 (p <0.001), top-10 6/10 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 0.99 (p <0.001), top-10 9/12 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 0.98 (p <0.001), top-10 9/10 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.51 (p <0.001), top-10 0/12 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | 0.43 (p <0.001), top-10 0/10 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 0.98 (p <0.001), top-10 8/10 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 0.99 (p <0.001), top-10 8/10 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.51 (p <0.001); partial 0.44 (p <0.001) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.41 (p <0.001); partial 0.33 (p 0.001) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.59 (p <0.001); partial 0.50 (p <0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.40 (p <0.001); partial 0.27 (p 0.006) |

**Headline vs main spec:** RQ1 unchanged; RQ2 weaker; RQ3 (partial rho) Weighted degree unchanged, Eigenvector unchanged, PageRank weaker, Betweenness unchanged.

### Decay delta = 0.7 (`delta_0.7`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9442, strong-link cut-off = 0.8393, strong links = 1418; delta = 0.7, tau percentile = 90, strong-link percentile = 75, later rounds = strong, centrality = strong network.

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 67.79 |
| RQ1 | Triggers with total reach = 0 | 23 | 23 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 28 |
| RQ1 | rho(total reach, exposure) | 0.79 | 0.14 |
| RQ1 | Total reach vs main spec | - | 0.92 (p <0.001), top-10 11/21 |
| RQ1 | Exposure vs main spec | - | 0.48 (p <0.001), top-10 1/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.95 (p <0.001), top-10 10/12 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.94 (p <0.001), top-10 11/11 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 0.95 (p <0.001), top-10 7/12 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 1.00 (p <0.001), top-10 11/11 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.49 (p <0.001), top-10 0/12 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | 0.16 (p 0.097), top-10 0/11 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 1.00 (p <0.001), top-10 10/10 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 1.00 (p <0.001), top-10 10/10 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.32 (p 0.001); partial 0.26 (p 0.008) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.25 (p 0.009); partial 0.21 (p 0.034) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.42 (p <0.001); partial 0.35 (p <0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.26 (p 0.008); partial 0.17 (p 0.092) |

**Headline vs main spec:** RQ1 weaker; RQ2 weaker; RQ3 (partial rho) Weighted degree weaker, Eigenvector weaker, PageRank weaker, Betweenness weaker.

### Distress threshold at the 95th percentile (`tau_95`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9561, strong-link cut-off = 0.8393, strong links = 1418; delta = 0.5, tau percentile = 95, strong-link percentile = 75, later rounds = strong, centrality = strong network.

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 48.92 |
| RQ1 | Triggers with total reach = 0 | 23 | 38 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 40 |
| RQ1 | rho(total reach, exposure) | 0.79 | 0.54 |
| RQ1 | Total reach vs main spec | - | 0.75 (p <0.001), top-10 10/21 |
| RQ1 | Exposure vs main spec | - | 0.94 (p <0.001), top-10 15/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.94 (p <0.001), top-10 9/10 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.90 (p <0.001), top-10 7/16 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 0.99 (p <0.001), top-10 10/10 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 0.96 (p <0.001), top-10 13/16 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.70 (p <0.001), top-10 0/10 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | 0.26 (p 0.008), top-10 0/16 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 0.94 (p <0.001), top-10 9/13 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 0.99 (p <0.001), top-10 11/13 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.77 (p <0.001); partial 0.58 (p <0.001) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.52 (p <0.001); partial 0.21 (p 0.033) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.81 (p <0.001); partial 0.68 (p <0.001) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.51 (p <0.001); partial 0.28 (p 0.005) |

**Headline vs main spec:** RQ1 weaker; RQ2 stronger; RQ3 (partial rho) Weighted degree stronger, Eigenvector weaker, PageRank stronger, Betweenness unchanged.

### Later rounds along the full network (`later_rounds_full`)

Values used: n = 107 banks, s0 = 0.6508, tau = 0.9442, strong-link cut-off = 0.8393, strong links = 1418; delta = 0.5, tau percentile = 90, strong-link percentile = 75, later rounds = full, centrality = strong network.

| RQ | Measure | Main spec | This run |
|---|---|---|---|
| RQ1 | Mean total reach | 60.12 | 79.50 |
| RQ1 | Triggers with total reach = 0 | 23 | 23 |
| RQ1 | Triggers with indirect reach = 0 | 28 | 25 |
| RQ1 | rho(total reach, exposure) | 0.79 | -0.61 |
| RQ1 | Total reach vs main spec | - | 0.83 (p <0.001), top-10 15/21 |
| RQ1 | Exposure vs main spec | - | -0.30 (p 0.002), top-10 1/21 |
| RQ2 | Total reach: linear mapping | 0.94 (p <0.001), top-10 13/21 | 0.77 (p <0.001), top-10 20/20 |
| RQ2 | Exposure: linear mapping | 0.74 (p <0.001), top-10 21/21 | 0.72 (p <0.001), top-10 22/22 |
| RQ2 | Total reach: convex mapping | 0.99 (p <0.001), top-10 18/21 | 0.75 (p <0.001), top-10 20/20 |
| RQ2 | Exposure: convex mapping | 0.97 (p <0.001), top-10 16/21 | 0.92 (p <0.001), top-10 22/22 |
| RQ2 | Total reach: single-round model | 0.58 (p <0.001), top-10 0/21 | 0.60 (p <0.001), top-10 0/20 |
| RQ2 | Exposure: single-round model | 0.36 (p <0.001), top-10 0/21 | -0.59 (p <0.001), top-10 0/22 |
| RQ2 | Indirect reach: linear mapping | 0.89 (p <0.001), top-10 8/11 | 1.00 (p <0.001), top-10 12/17 |
| RQ2 | Indirect reach: convex mapping | 0.99 (p <0.001), top-10 10/11 | 1.00 (p <0.001), top-10 14/17 |
| RQ3 | Weighted degree | rho 0.57 (p <0.001); partial 0.48 (p <0.001) | rho 0.17 (p 0.089); partial 0.13 (p 0.201) |
| RQ3 | Eigenvector | rho 0.46 (p <0.001); partial 0.33 (p 0.001) | rho 0.11 (p 0.245); partial 0.11 (p 0.277) |
| RQ3 | PageRank | rho 0.67 (p <0.001); partial 0.58 (p <0.001) | rho 0.31 (p 0.001); partial 0.29 (p 0.003) |
| RQ3 | Betweenness | rho 0.43 (p <0.001); partial 0.26 (p 0.008) | rho 0.15 (p 0.113); partial 0.11 (p 0.276) |

**Headline vs main spec:** RQ1 reversed; RQ2 unchanged; RQ3 (partial rho) Weighted degree weaker, Eigenvector weaker, PageRank weaker, Betweenness weaker.

## 8. Figures

- `output/figures/total_reach_hist.png`: Histogram of total reach across the 107 trigger banks (main spec), 5-bank bins.
- `output/figures/exposure_hist.png`: Histogram of exposure across the 107 banks (main spec), 5-simulation bins.
- `output/figures/centrality_vs_indirect.png`: Four-panel scatter of each strong-link centrality measure against indirect reach (main spec).
- `output/figures/top10_direct_indirect.png`: Stacked bars of direct and indirect reach for the top-10 banks by total reach, including all banks tied at 10th place (main spec).

## 9. Plain-English summary

**RQ1.**
Total reach ranges from 0 to 94 banks, with a mean of 60.12 and a median of 81. 23 of the 107 trigger banks distress no other bank, and 28 have no indirect reach (5 of these distress banks in round 1 only). The highest total reach is 94 (Groupe Crédit Agricole). The highest exposure is 79 of 106 simulations (AIB Group plc). The Spearman correlation between total reach and exposure is 0.79 (p <0.001).

**RQ2.**
Direct reach is identical under the logistic, linear and convex mappings for every trigger (rho = 1.00 and 1.00). Indirect reach has rho = 0.89 with the linear mapping and 0.99 with the convex mapping. For total reach, rho with the main ranking is 0.94 (linear), 0.99 (convex) and 0.58 (single-round), with top-10 overlaps of 13/21, 18/21 and 0/21. For exposure, the corresponding rho values are 0.74, 0.97 and 0.36, with top-10 overlaps of 21/21, 16/21 and 0/21.

**RQ3.**
On the strong-link network, the Spearman correlation between centrality and indirect reach ranges from 0.43 (Betweenness) to 0.67 (PageRank), and 4 of the 4 measures have p < 0.05. After controlling for log total assets, CET1 ratio and direct reach, the partial correlation ranges from 0.26 (Betweenness) to 0.58 (PageRank), and 4 of the 4 have p < 0.05. On the complete network the partial correlations range from 0.37 to 0.74.

## 10. Anomalies and caveats

- **Ties in the top/bottom tables.** All banks tied with the 10th bank are kept, so top-10 total reach has 21 banks; bottom-10 total reach has 23 banks; top-10 exposure has 21 banks. Ranks are average ranks (1 = highest). The top-10 overlap in RQ2 is reported as k / (size of the reference top-10 set) for the same reason, so it can exceed 10.
- **Few distinct values.** Main-spec exposure takes only 31 distinct values and total reach 25, so rankings contain many ties. Spearman rho handles these with average ranks.
- **Zero reach.** Every trigger with direct reach 0 also has total reach 0, because later rounds start only from banks distressed in round 1 (23 triggers). A further 5 triggers distress banks in round 1 but none later: Revolut Holdings Europe UAB (direct 1), Volkswagen Financial Services AG (direct 1), LGT Group Foundation (direct 1), Bank of Cyprus Holdings Public Limited Company (direct 1), RCI Banque (direct 1).
- **Why direct reach does not depend on the mapping.** All three mappings (logistic, linear, convex) only ever increase as similarity increases, and tau is always set at the same percentile of each mapping's own values. So whichever mapping is used, round 1 distresses exactly the banks whose similarity to the trigger is above the same similarity level. That makes direct reach, and the whole single-round model, identical across mappings (validation check 7). Any difference between mappings in indirect or total reach comes only from rounds 2 onwards, where the risk passed on by several distressed banks is added up and the shape of the mapping changes those sums.
- **Single-round model.** Its total reach equals the main spec's direct reach for every trigger, and its indirect reach is always 0. That is why no indirect-reach comparison is reported for it.
- **Reference results.** delta = 1.0 on the full network: 76.6% of triggers distress all 106 banks, 21.5% distress none. Main spec: 21.5% none, mean total reach 60.12. Both are within the tolerance used (2 percentage points, 1 bank).
- **Without the four public-sector banks.** Matched names: BNG Bank N.V.; SFIL S.A.; Kommuninvest - Grupp; Kuntarahoitus Oyj. s0, tau, the strong-link cut-off and all four centralities are recomputed on the 103-bank sample. Comparisons with the main spec use the 103 banks present in both, and the main top-10 is re-taken on those 103 banks.
- **Centrality on the complete network.** The cascade is identical to the main spec, so only RQ3 changes. RQ1 and RQ2 are marked n/a.
- **pingouin.** It is not installed (and was not installed), so the partial correlation is computed only by the rank, OLS-residual and Pearson method described in the brief.
- **Headline labels.** 'Unchanged / weaker / stronger / reversed' compare a single correlation with the main spec. For RQ1 it is rho(total reach, exposure); for RQ2 it is the smallest of the three rho values for total reach (linear, convex, single-round); for RQ3 it is the partial rho for each measure. The label is 'stronger' or 'weaker' if |rho| changes by at least 0.05, and 'reversed' if the sign flips and both values have |rho| >= 0.05. These cut-offs were my choice, not part of the brief.
- **Other assumptions.** Percentiles use numpy's default linear interpolation. 'rounds' is the last round in which a bank became newly distressed (0 if none). Standard deviations are sample standard deviations (ddof = 1). p-values below 0.0005 are shown as <0.001. Linear and convex runs keep the strong links defined on similarity and recompute tau on their own values.
- **Reach-exposure correlation across runs** (rho, then number of distinct exposure values): main 0.79 (31), no_public_banks 0.77 (31), strong_link_70 0.47 (20), strong_link_80 0.87 (29), delta_1.0 -0.12 (8), delta_0.3 0.82 (37), delta_0.7 0.14 (16), tau_95 0.54 (31), later_rounds_full -0.61 (5). It is negative in: delta_1.0, later_rounds_full.
- **RQ3 partial correlations with p >= 0.05:** delta_1.0 Betweenness (0.13, p 0.202), delta_0.7 Betweenness (0.17, p 0.092), later_rounds_full Weighted degree (0.13, p 0.201), later_rounds_full Eigenvector (0.11, p 0.277), later_rounds_full Betweenness (0.11, p 0.276).
- **Same network in model and centrality.** In the main spec, rounds 2 onwards travel along the same strong-link network that the four centrality measures are computed on.
- **Bank names.** These names end in a digit in bank_metadata.csv (taken from TR_Metadata.xlsx) and are reported as they appear: Coöperatieve Rabobank U.A.2.
- **Cascade length.** Maximum rounds per run: main 8, no_public_banks 8, strong_link_70 7, strong_link_80 7, complete_centrality 8, delta_1.0 6, delta_0.3 5, delta_0.7 6, tau_95 8, later_rounds_full 5.
