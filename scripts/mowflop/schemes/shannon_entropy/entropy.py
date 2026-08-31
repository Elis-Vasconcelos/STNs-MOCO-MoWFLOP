"""Particionamento do espaço de busca por entropia de Shannon (Ochoa, Malan & Blum 2021, S5.4).

O esquema, fiel ao artigo:

1. ``T`` é um conjunto de trajetórias de busca para a mesma instância, cada uma
   possivelmente produzida por um algoritmo diferente.  ``S(T)`` é o conjunto
   de soluções *únicas* contidas nelas.
2. A partir de ``S(T)``, estima-se ``p(x_i = d)`` para cada posição ``i`` e
   calcula-se a entropia de Shannon ``H(x_i) = -sum_d p log2 p``.  O domínio
   aqui é binário, então ``H <= 1`` bit.
3. Ordena-se as posições por entropia não crescente numa lista ``L``.  O artigo
   desfaz empates aleatoriamente (ver seu Exemplo 1).
4. Mantêm-se as primeiras ``z`` posições, ``L_z``.  A localização de uma
   solução ``s`` é sua projeção ``s_z`` sobre ``L_z``; ``s`` e ``s'`` compartilham
   localização sse ``s_z == s'_z``.
5. O valor objetivo de uma localização é o melhor objetivo entre as soluções
   que caem nela: ``f(s_z) := min{f(s') : s' in S(T), s'_z = s_z}``.
6. ``z`` segue o *critério de área*: um particionamento de ``X%`` é o **maior**
   ``z`` em ``{1..n}`` tal que a área sob a curva de entropia da ``z``-ésima
   variável até a última seja pelo menos ``X%`` da área total.  ``X = 0%``
   portanto significa nenhum particionamento (``z = n``).

Alvo de regressão, reproduzido por :func:`area_partition_z` e
:func:`Partition.locations`: nos dados ``pmed7`` dos próprios autores (ACO +
BRKGA + ILS agrupados), ``|S(T)| = 423``, ``z(60%) = 19`` e o espaço
particionado tem ``312`` localizações -- os três números publicados no artigo
(Tabela 8 e o texto da S6.2).

Soluções são tratadas como o *conjunto de posições com valor 1*, que é a forma
natural das duas entradas que nos interessam: o MoWFLOP loga uma lista ordenada
de índices de candidatos ocupados, e os dados de p-mediana uma string binária
densa.  Para um domínio binário as duas representações carregam a mesma
informação, e duas soluções concordam em todas as posições retidas exatamente
quando seus conjuntos de uns, intersectados com as posições retidas, coincidem.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from hashlib import blake2b

Solution = frozenset[int]

LOCATION_PREFIX = "E"


def from_index_list(text: str) -> Solution:
    """Converte uma lista de índices (formato ``occupied`` do MoWFLOP) numa solução.

    Args:
        text: índices separados por espaço, ex. ``"17 227 270"``.

    Returns:
        Conjunto das posições ocupadas.
    """
    return frozenset(int(token) for token in text.split())


def from_binary_string(text: str) -> Solution:
    """Converte uma string binária (traço de p-mediana) numa solução.

    Args:
        text: string binária, ex. ``"0101..."``.

    Returns:
        Conjunto das posições que têm valor ``1``.
    """
    return frozenset(i for i, char in enumerate(text) if char == "1")


def position_entropy(solutions: list[Solution], n: int) -> list[float]:
    """Entropia de Shannon de cada posição sobre um conjunto de soluções únicas.

    Args:
        solutions: soluções distintas de ``S(T)``.
        n: número total de posições do espaço de busca.

    Returns:
        Lista de tamanho ``n`` com ``H(x_i)`` (em bits) para cada posição ``i``.

    Raises:
        ValueError: se ``solutions`` estiver vazio.
    """
    total = len(solutions)
    if total == 0:
        raise ValueError("cannot compute entropy of an empty solution set")
    # ones[i] = quantas soluções têm 1 na posição i
    ones = Counter()
    for solution in solutions:
        # para cada posição ocupada em solution, incrementa o contador de 1s correspondente
        ones.update(solution)
    entropy = []
    for position in range(n):
        k = ones.get(position, 0)
        value = 0.0
        if k:
            # calcula a probabilidade de 1 na posição i
            p = k / total
            value -= p * math.log2(p)
        if total - k:
            # calcula a probabilidade de 0 na posição i
            p = (total - k) / total
            value -= p * math.log2(p)
        entropy.append(value)
    return entropy


def rank_positions(
    entropy: list[float], tie_break: str = "random", seed: int | None = None
) -> list[int]:
    """Ordena as posições por entropia não crescente.

    Args:
        entropy: entropia de cada posição, na ordem do índice original.
        tie_break: ``"random"`` (padrão) segue o artigo -- empates são
            desfeitos aleatoriamente, com semente para o resultado ser
            reprodutível; ``"index"`` é a variante determinística, usada só
            nos testes de regressão contra os números publicados.
        seed: semente do gerador aleatório quando ``tie_break="random"``.

    Returns:
        Lista de índices de posição, da maior para a menor entropia.

    Raises:
        ValueError: se ``tie_break`` não for ``"index"`` nem ``"random"``.
    """
    if tie_break not in {"index", "random"}:
        raise ValueError(f"unknown tie_break: {tie_break!r}")
    order = list(range(len(entropy)))
    if tie_break == "random":
        # embaralha antes: como o sort abaixo é estável, os empates saem em ordem aleatória
        random.Random(seed).shuffle(order)
        return sorted(order, key=lambda i: -entropy[i])
    return sorted(order, key=lambda i: (-entropy[i], i))


def area_partition_z(entropy_desc: list[float], percent: float) -> int:
    """Calcula ``z`` para um particionamento de ``X%``, a partir da curva de entropia.

    É o maior ``z`` tal que a área da ``z``-ésima variável até a última seja
    pelo menos ``X%`` da área total.  As somas de sufixo são não crescentes em
    ``z``, então o conjunto viável é um prefixo e a resposta é o seu último
    elemento.

    Args:
        entropy_desc: entropia já ordenada de forma não crescente (``L`` do
            artigo).
        percent: critério de área ``X``, em ``[0, 100]``.

    Returns:
        O maior ``z`` que satisfaz o critério de área; ``0`` se nenhum ``z``
        satisfizer (curva vazia).

    Raises:
        ValueError: se ``percent`` estiver fora de ``[0, 100]``.
    """
    if not 0 <= percent <= 100:
        raise ValueError(f"percent must be in [0, 100], got {percent}")
    n = len(entropy_desc)
    total = sum(entropy_desc)
    if total <= 0:
        # não há curva pra trabalhar
        return n
    target = percent / 100.0 * total
    suffix = 0.0
    # soma acumulada de trás pra frente = área sob a curva da posição z até a última
    for z in range(n, 0, -1):
        suffix += entropy_desc[z - 1]
        if suffix >= target:
            return z  # decrescente, então o primeiro z que satisfaz a condição é o maior
    return 0


def location_id(projection: Solution) -> str:
    """Id curto e estável para uma localização.

    A projeção pode ter centenas de posições; escrevê-la por extenso nos
    arquivos de trajetória infla demais os arquivos, então o id é um digest de
    64 bits e a projeção completa fica na tabela auxiliar escrita por
    :mod:`mowflop.emit`.

    Args:
        projection: conjunto de posições retidas (``s_z``).

    Returns:
        Id no formato ``"E<16 hex>"``.
    """
    key = ",".join(str(position) for position in sorted(projection))
    digest = blake2b(key.encode("utf-8"), digest_size=8).hexdigest()
    return f"{LOCATION_PREFIX}{digest}"


@dataclass
class Partition:
    """Um particionamento por entropia concreto do espaço de busca de uma instância.

    Attributes:
        n: número total de posições do espaço de busca.
        entropy: entropia de cada posição, na ordem do índice original.
        order: posições ordenadas por entropia não crescente (``L`` do artigo).
        z: número de posições retidas.
        percent: critério de área usado para obter ``z``, se foi esse o caminho.
        tie_break: política de desempate usada para gerar ``order``.
        seed: semente do desempate aleatório, se ``tie_break="random"``.
    """

    n: int
    entropy: list[float]
    order: list[int]
    z: int
    percent: float | None = None
    tie_break: str = "random"
    seed: int | None = None
    keep: frozenset[int] = field(init=False)  # posições de maior entropia que serão usadas no particionamento

    def __post_init__(self) -> None:
        if not 0 <= self.z <= self.n:
            raise ValueError(f"z must be in [0, {self.n}], got {self.z}")
        self.keep = frozenset(self.order[: self.z])

    def project(self, solution: Solution) -> Solution:
        """Restringe uma solução às posições retidas (``s_z``).

        Args:
            solution: solução completa.

        Returns:
            A solução restrita ao conjunto ``keep``.
        """
        return solution & self.keep

    def assign(self, solution: Solution) -> str:
        """Id da localização em que a solução cai.

        Args:
            solution: solução completa.

        Returns:
            Id da localização (ver :func:`location_id`).
        """
        return location_id(self.project(solution))

    def locations(self, solutions: list[Solution]) -> set[Solution]:
        """Localizações distintas alcançadas por um conjunto de soluções.

        Args:
            solutions: soluções a projetar.

        Returns:
            Conjunto das projeções distintas (uma por localização).
        """
        return {self.project(solution) for solution in solutions}

    @property
    def entropy_desc(self) -> list[float]:
        """Entropia na ordem de ``order`` (não crescente)."""
        return [self.entropy[i] for i in self.order]

    def tie_size_at_z(self) -> int:
        """Quantas posições empatam com a entropia da ``z``-ésima.

        Um ``z`` que cai dentro de um bloco de empate grande significa que o
        conjunto retido é em boa parte arbitrário -- o artigo desfaz esses
        empates aleatoriamente.

        Returns:
            Tamanho do bloco de empate na fronteira de ``z``; ``0`` se ``z=0``.
        """
        if self.z == 0:
            return 0
        cutoff = self.entropy[self.order[self.z - 1]]
        return sum(1 for value in self.entropy if math.isclose(value, cutoff))

    def describe(self) -> dict:
        """Resumo serializável do particionamento, para relatórios e logs.

        Returns:
            Dicionário com as estatísticas do particionamento.
        """
        values = self.entropy_desc
        return {
            "scheme": "entropy",
            "n": self.n,
            "z": self.z,
            "percent": self.percent,
            "tie_break": self.tie_break,
            "seed": self.seed,
            "entropy_total": sum(values),
            "entropy_max": max(values) if values else 0.0,
            "positions_nonzero": sum(1 for value in values if value > 0.0),
            "tie_size_at_z": self.tie_size_at_z(),
        }


def build_partition(
    solutions: list[Solution],
    n: int,
    percent: float | None = None,
    z: int | None = None,
    tie_break: str = "random",
    seed: int | None = None,
) -> Partition:
    """Constrói o particionamento por entropia de ``S(T)``.

    Args:
        solutions: soluções únicas de ``S(T)``.
        n: número total de posições do espaço de busca.
        percent: critério de área ``X%``; dê exatamente um de ``percent``/``z``.
        z: número fixo de posições a reter; dê exatamente um de ``percent``/``z``.
        tie_break: política de desempate do ranking de entropia (ver
            :func:`rank_positions`).
        seed: semente do desempate aleatório.

    Returns:
        O :class:`Partition` resultante.

    Raises:
        ValueError: se não for dado exatamente um de ``percent``/``z``.
    """
    if (percent is None) == (z is None):
        raise ValueError("give exactly one of percent or z")
    entropy = position_entropy(solutions, n)
    order = rank_positions(entropy, tie_break=tie_break, seed=seed)
    if z is None:
        z = area_partition_z([entropy[i] for i in order], percent)
    return Partition(
        n=n, entropy=entropy, order=order, z=z, percent=percent,
        tie_break=tie_break, seed=seed,
    )
