# `mowflop` — particionamento do espaço de busca para as STNs do MoWFLOP

Este pacote roda **antes** do pipeline em R. Ele lê os logs brutos da
campanha, mapeia cada solução logada para uma *localização* de um espaço de
busca particionado, e escreve os arquivos exatamente no formato que o
`scripts/create .R` já lê. A ideia é que o modelo particionado e o não
particionado atravessem o mesmo código R, então qualquer diferença nas
métricas vem só do particionamento.

## Mapa da pasta

### Núcleo do pipeline

> **De preferência não mexer nestes módulos.** Eles são comuns a todos os
> particionamentos, é justamente por atravessarem o mesmo código que as
> métricas ficam comparáveis. As exceções são mudar os parâmetros de execução
> e corrigir algum problema identificado.

| módulo | o que faz | quando mexer |
|---|---|---|
| `partition.py` | orquestra tudo: lê os logs, aplica um esquema, calcula a frente de referência e chama o `emit`. É o ponto de entrada (`python -m mowflop.partition`). | parâmetros de execução: constantes no topo do arquivo ou env vars `MOWFLOP_*` |
| `io_raw.py` | leitura dos logs brutos (`raw_results/meta_heuristics_stn_windcorrected/`): `raw_root`, `discover`, `inventory`, `load_trajectories`, `load_candidates`. | mudou o layout/nome das pastas de `raw_results/`, ou precisa de um novo recorte dos logs |
| `reference_front.py` | monta a frente de Pareto de referência: pontos da nossa campanha **∪** `external_points()` do `raw_results/wflopcec26/`. `pareto_front()` é genérico (não dominado sobre o que receber). | ajuste na frente de referência ou nova fonte externa |
| `emit.py` | escreve os arquivos no formato que o `create .R` lê (ordem das 9 colunas + convenção do nome do arquivo). Contém `canonical_objectives`. | com muito cuidado — ver *Invariantes* abaixo |
| `geometry.py` | geometria da instância (área `A`, nº de turbinas `τ`, piso `σ`) para o esquema `grid`. Lê do repo irmão `STN_MoWFLOP/instances/site/<inst>/` (`$MOWFLOP_INSTANCES` sobrescreve). | mudou a fonte da geometria das instâncias |
| `validate_r_input.py` | confere um dataset já emitido antes de rodar o R, reproduzindo em pandas os passos onde o `create .R` falha tarde e feio. | rodar como checagem; raramente precisa editar |

### Esquemas de particionamento (`schemes/`)

| módulo | o que faz | quando mexer |
|---|---|---|
| `schemes/schemes.py` | registro dos esquemas intercambiáveis (`raw`, `entropy`, `grid`) + `build_scheme()`. Cada esquema implementa `assign()` / `project()` / `describe()`. | **é aqui que entra um esquema novo** (ver *Adicionar um esquema*) |
| `schemes/shannon_entropy/entropy.py` | esquema `entropy` — entropia de Shannon (Ochoa, Malan & Blum 2021, §5.4). | mexer no esquema de entropia |
| `schemes/shannon_entropy/diagnose_entropy.py` | diagnóstico da RQ1: curva de entropia e o `z` de cada critério de área. Standalone. | investigar se a entropia se aplica a uma instância |
| `schemes/grid/grid.py` | esquema `grid` — assinatura de ocupação numa grade de lado `ℓ = max(κ·√(A/τ), σ)`. É a contribuição central da tese. | mexer no esquema de grade |

### Wrappers dos scripts R (`run_scripts/`)

Servem para rodar os scripts R em lote (para uma rodada manual e avulsa,
basta editar o caminho no próprio `.R` e rodá-lo). Todos seguem o mesmo padrão:
copiam o `.R` para um temporário, reescrevem **só** as constantes de
pasta/parâmetro, conferem com um `diff` que nada mais mudou e rodam a cópia.
Não editam o script original.

| módulo | roda | flags |
|---|---|---|
| `run_scripts/run_create_r.py` | `create .R` (Ochoa, sem modificar) | `--tag` |
| `run_scripts/run_metrics_r.py` | `metrics.R` (Ochoa original, benchmark rho-mnk; algumas colunas saem `NA`) | `--tag --algo` |
| `run_scripts/run_stn_metrics_r.py` | `metrics_stn_mowflop.R` (já parseia os nomes do MoWFLOP) | `--tag --algo` |
| `run_scripts/run_shared_alg_r.py` | `shared_alg.R` (MOEAD + NSGA2 juntos) | `--tag` |
| `run_scripts/run_plot_r.py` | `plot.R` (PNGs, layouts `of`/`fd`) | `--tag --layout` |
| `run_scripts/run_compare_r.py` | mosaico comparativo 2×3 por instância | `--instance --layout` |


## Invariantes — o que **não** pode mudar

- **`create .R`, `metrics.R`, `metrics_stn_mowflop.R` e `shared_alg.R` nunca são
  editados.** Os wrappers em `run_scripts/` abortam se o `diff` mostrar
  qualquer mudança além das constantes de pasta/parâmetro. `plot.R` é a única
  exceção (patch de título, commit `80600fa`) — e mesmo assim os wrappers
  cortam o prefixo do arquivo *atual*, não de um original fixado.
- **Um objetivo canônico por localização** (`emit.canonical_objectives`). Na STN
  cada localização tem de virar **um** nó. Mas o `create .R` não identifica o nó
  pelo `Solution1` (o id da localização) e sim pela tupla
  `(f1, f2, Solution1, Vector)`. Num espaço particionado a mesma localização é
  visitada por muitas soluções, cada uma com seu vetor objetivo; se cada
  registro levasse o seu próprio `(f1, f2)`, o `Solution1` apareceria sob vários
  pares objetivo e o `create .R` quebraria essa localização em vários nós,
  desfazendo o particionamento sem erro nenhum. Por isso o `emit` colapsa toda
  localização num único vetor objetivo representativo — sempre uma solução que
  de fato passou por ali, escolhida por "estar na frente de referência primeiro,
  depois ordem lexicográfica `(f_cost, -f_power)`" (a leitura multiobjetivo do
  `f(s_z) := min{f(s')}` do artigo).
- **Self-loop no fim de cada trajetória.** A última gravação de cada
  `(Run, Vector)` aponta para si mesma. Não é regra nova do `mowflop`: os
  `_post.txt` originais do rho-mnk já fazem `Solution1 == Solution2` em todo
  passo de estagnação, e o `create .R` foi escrito em cima disso, pois precisa que
  todo endpoint de aresta exista em `nodes`, senão `graph_from_data_frame`
  falha ("Some vertex names in `d` are not listed in `vertices`"). O `emit`
  só reproduz a convenção.
- **Formato do `emit.py`:** a ordem das 9 colunas e a convenção do nome do
  arquivo — o `create .R` depende das duas posicionalmente.

## Decisões já tomadas (não re-derivar)

- **Frente de referência = nossa campanha ∪ `wflopcec26`.** `Position="Pareto"`
  reflete o melhor que o grupo achou, não só o nosso MOEA/D e NSGA-II.
  (`MOWFLOP_EXTERNAL_FRONT=0` desliga isso e sufixa a tag com `noext`.)
- **κ global = 0.5 (fino) / 1.0 (adequado) / 2.0 (grosseiro)**, escolhidos
  *antes* de rodar, pelo teto de degenerescência no menor `τ` (`ns48`). Não
  varrer κ por instância — κ é meta-parâmetro global.
- **Desempate da entropia = `random`** (com semente, reprodutível). O `index`
  determinístico existe só para os testes de regressão.
- **Dados vendorizados no repo:** `raw_results/meta_heuristics_stn_windcorrected/`
  (logs da campanha) e `raw_results/wflopcec26/` (runs do grupo). Só o
  `geometry.py` ainda depende do `STN_MoWFLOP` irmão.

## Rodar o pipeline

`x60` = esquema entropy, critério de área 60%. `g0.5`/`g1.0`/`g2.0` = esquema
grid nesse κ. `raw` = sem particionar.

1. **Particionar** (Python): edite as constantes no topo de
   `mowflop/partition.py` (ou use as env vars `MOWFLOP_*`) e rode
   `../.venv/bin/python -m mowflop.partition` a partir de `scripts/`. Sai em
   `data/`, `pf/` e `locations/`.
2. **Rodar os scripts R** (`create .R` → `metrics.R` / `metrics_stn_mowflop.R`
   → `shared_alg.R` → `plot.R`, nessa ordem): edite as variáveis de caminho no
   topo de cada script para apontar para a tag do passo 1, crie as pastas de
   saída (`stns/`, `metrics/`, `plots/`) e rode com `Rscript` a partir da raiz
   do repo. Sem esquema particionado, `raw` passa pelos mesmos scripts.

Editar esses `.R` e **commitar** quebra o invariante "os `.R` nunca são
editados" — faça a edição só numa cópia local, ou desfaça com
`git checkout -- '<arquivo>'`. Os wrappers em `run_scripts/` automatizam
exatamente esse passo 2 (numa cópia temporária) quando é preciso rodar em
lote; a varredura completa está em `scripts/run_kappa_sweep.sh` e a campanha de
entropia em `scripts/run_entropy_campaign.sh`.

## Adicionar um esquema de particionamento

1. Crie uma subpasta em `schemes/` (como `schemes/grid/`) com a lógica.
2. Em `schemes/schemes.py`, implemente uma classe com `assign(solution)`,
   `project(solution)` e `describe()`, e registre-a em `build_scheme()`.
3. Nada a jusante muda: `partition.py`, `emit.py` e o pipeline em R já
   consomem qualquer esquema pelo mesmo formato de saída.

## Setup

```bash
python3 -m venv --without-pip .venv
curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python -
.venv/bin/pip install -r requirements.txt
```
