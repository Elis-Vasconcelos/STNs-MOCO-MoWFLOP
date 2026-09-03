# RQ1 — curvas de entropia das instâncias esparsas 506–513

Curvas de entropia de Shannon por posição (estilo Fig. 5 de Ochoa, Malan &
Blum 2021) para as 8 instâncias do *single-site sparsity sweep* (RQ1),
geradas pelo mesmo caminho de código que emite as STNs:

```
scripts/  ->  ../.venv/bin/python -m mowflop.schemes.shannon_entropy.diagnose_entropy \
                --all --raw-root <só as 8 instâncias> --figs
```

- **Fonte dos dados:** `raw_results/meta_heuristics_stn_windcorrected/`
  (campanha wind-corrected, Bambu, set/2026). `tie_break=random`, `seed=0`.
- **Config:** só `p100_i50` (a varredura rodou só essa).
- **S(T):** soluções únicas de MOEA/D + NSGA-II agrupados, 60 runs por
  instância — **exceto `513_e-05`**, que é **só MOEA/D (30 runs)**: os runs
  NSGA-II dessa célula ainda estavam executando no Bambu quando isto foi
  gerado. Regenerar `513_e-05` quando a campanha fechar.

## As 8 instâncias

Sítio sintético único compartilhado; só variam τ e a densidade τ/n.

| família | τ | densidade (e-02 → e-05) |
|---|---|---|
| 506 507 508 509 | 5 | 0.083 → 0.0083 → 0.00083 → 0.000083 |
| 510 511 512 513 | 15 | 0.014 → 0.0059 → 0.00077 → 0.000081 |

## Como ler

- Eixo x (log): posição, ordenada por `H(x_i)` decrescente (posto em `L`).
- Linhas tracejadas: `z` de cada critério de área (50/60/70/80/90 %).
- Título: fração de posições com `H = 0` e maior bloco de empate.

## O que mostram (degenerescência RQ1)

Conforme a densidade cai (mesma τ, mais posições), o particionamento por
entropia colapsa — ver `summary.csv`:

- `fraction_zero`: 0.00 → **0.93** (τ=5) / 0.00 → **0.92** (τ=15). Quase
  toda posição nunca é ocupada, então `H = 0`.
- `largest_tie_block`: 4 → **55 767** (τ=5) / 42 → **169 362** (τ=15). O
  desempate aleatório passa a decidir quase tudo.
- `z_60` deixa de ser um corte informativo (poucas posições carregam toda
  a área da curva).

`summary.csv` — uma linha por instância, com `n`, τ, densidade,
`unique_solutions`, estatísticas da curva e `z` de cada critério de área.
Os CSVs completos das curvas e os PDFs ficam em `reports/rq1_entropy/`.
