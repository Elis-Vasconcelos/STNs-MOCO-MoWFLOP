# Métricas das STNs por instância

Métricas de todas as STNs da campanha de 2026-10-05, a mesma usada no artigo.
Variante `ext`: conjunto de referência inclui as execuções da CEC com o mesmo
cenário de vento. É com ela que a Tabela II do artigo bate.

Código: STNs-MOCO-MoWFLOP, commit `d5b7af9d`. Execuções 0 a 9 em todas as
instâncias.

## Arquivos

| arquivo | uma linha por |
|---|---|
| `stn_metrics_todas.csv` | instância × esquema × nível × frente × algoritmo × p × run |
| `shared_alg_todas.csv` | instância × esquema × nível × frente × p × run (compara os dois algoritmos) |
| `partition_metrics_todas.csv` | instância × esquema × nível × frente × algoritmo × p × run |
| `rank_stab_todas.csv` | instância × p × X, ver a seção Rank stability |
| `arquivos/rank_stab/` | os 3 resumos do rank stability |

Os 96 CSVs exatamente como o pipeline gerou, um por configuração, sem nenhuma alteração, estão em `sharing/campanhas/full_ext_<esquema>_<família>_2026-10-05/metrics/`.

Os três `_todas.csv` são só a junção desses 96 CSVs, com estas colunas a mais no começo:

- `paper_no`: número da instância no artigo, de 1 a 14. Vazio para ns510 a ns513, que não estão no artigo.
- `tau`, `n_positions`: número de turbinas e de posições candidatas.
- `scheme`: `entropy` (Shannon) ou `grid`.
- `level`: x para entropia, 60, 70 ou 80. κ para grade, 0.5, 1.0 ou 2.0.
- `front`: `aggregated` junta as 10 execuções numa STN só, `run` = 0. `per_scenario` é uma STN por execução, `run` = r00 a r09, cada uma com seu cenário de vento.
- `family`: `original` (instâncias da CEC) ou `sparse` (ns506 a ns513).
- `tag`: o nome da configuração no pipeline.

`p` é o número de vetores de peso, 10, 50 ou 100.

## Métricas

`stn_metrics_todas.csv`:

| coluna | definição |
|---|---|
| `nodes` | número de nós |
| `disc_rate` | nós / total de passos registrados nas trajetórias |
| `edge_ratio` | arestas / nós |
| `shared_vec` | fração dos nós visitados por mais de um vetor de peso |
| `pareto` | número de nós que estão no conjunto de referência |
| `par_strength` | fração das trajetórias, pares (execução, vetor), que passam por algum nó Pareto |
| `n_end` | fração dos nós que são fim de trajetória fora do conjunto Pareto |
| `path_par` | mediana, entre os nós de início que chegam a um nó Pareto, do menor caminho até ele |
| `path_par_reach` | fração dos nós de início que chegam a algum nó Pareto |

`shared_alg_todas.csv`: `shared_alg` é a fração das localizações visitadas pelos
dois algoritmos. `n_moead`, `n_nsga2`, `n_union` são os nós de cada um e da união.

`partition_metrics_todas.csv`:

| coluna | definição |
|---|---|
| `density` | tau / n_positions |
| `nodes_raw` | layouts distintos, ou seja, nós sem particionamento |
| `R` | 1 − nodes / nodes_raw, quanto o particionamento junta |
| `D` | diâmetro médio de cada localização no espaço objetivo normalizado, ponderado pelas visitas |
| `step_len` | tamanho médio de uma aresta em turbinas movidas, dividido por 2τ. Só existe na grade |

## Rank stability

`rank_stab_todas.csv`: uma linha por instância × p × X, 18 × 3 × 3 = 162 linhas.
Os resumos do script, sem alteração, estão em `arquivos/rank_stab/summary_x60.csv`,
`summary_x70.csv` e `summary_x80.csv`.

Gerado em 2026-11-17 com `rank_stability.py` do Arthur, sem alteração, sobre as
mesmas execuções 0 a 9 da campanha. As 10 execuções são divididas em duas metades,
0 a 4 e 5 a 9, com MOEA/D e NSGA-II juntos. A entropia de cada posição é calculada
separadamente em cada metade.

| coluna | definição |
|---|---|
| `rank_stab` | correlação de Spearman entre as entropias das posições nas duas metades. Perto de 1, as metades dão o mesmo ranking. Perto de 0, o ranking depende das execuções sorteadas |
| `rank_stab_active` | o mesmo Spearman, só nas posições com entropia > 0 em alguma metade. Posições com entropia 0 nas duas metades empatam e inflam o `rank_stab` |
| `rank_stab_p`, `rank_stab_active_p` | valor-p do teste de Spearman. Com milhares de posições ele é minúsculo para qualquer correlação não nula |
| `positions_active` | número de posições com entropia > 0 em alguma metade |
| `z_h1`, `z_h2` | posições retidas pelo critério de área de X% em cada metade |
| `retained_shared` | posições retidas pelas duas metades |
| `retained_overlap` | `retained_shared` / média de `z_h1` e `z_h2`. 1 = as metades retêm as mesmas posições |
| `retained_overlap_random` | o valor esperado de `retained_overlap` se cada metade sorteasse suas posições ao acaso |

`rank_stab` e `rank_stab_active` não dependem de X. Só as colunas `z_*` e `retained_*` mudam.
O artigo usa a instância 4 com p = 100 e X = 70: `rank_stab` = 0,14 e `retained_overlap` = 0,28.

## Cuidados

- Os nós Pareto usam igualdade exata com 6 casas decimais contra o conjunto de
  referência, e o logger só guarda parte do arquivo final de cada execução.
  Então `pareto`, `par_strength` e `path_par` refletem em parte essa amostragem.
- Na frente `aggregated` o conjunto de referência é a união das frentes de cada
  cenário na escala normalizada, não um único conjunto não dominado.
- `path_par` fica vazio quando nenhum nó de início chega ao conjunto Pareto.
  `path_par_reach` fica vazio quando a STN não tem nenhum nó de início.
