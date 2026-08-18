"""Esquemas de particionamento intercambiáveis.

Um esquema é qualquer coisa que mapeia uma solução para o id de uma
localização.  Manter esse o único ponto de variação é o que torna a comparação
justa: todo esquema, mais abaixo no pipeline, produz o mesmo formato de
arquivo, então o pipeline em R é byte a byte idêntico entre esquemas e
qualquer diferença de métrica vem só do particionamento.

Implementados aqui: ``entropy`` (Ochoa, Malan & Blum 2021) e ``raw`` (sem
particionamento, Ochoa et al. 2023).  O esquema de assinatura de ocupação e as
variantes de Hamming se encaixam implementando os mesmos dois métodos.
"""

from __future__ import annotations

from hashlib import blake2b

from . import entropy as entropy_mod
from .entropy import Solution

RAW_PREFIX = "R"


class RawScheme:
    """Sem particionamento: uma localização por solução distinta (a identidade)."""

    name = "raw"

    def assign(self, solution: Solution) -> str:
        """Id da localização de uma solução, sem particionamento.

        Args:
            solution: solução completa.

        Returns:
            Id no formato ``"R<16 hex>"``, um por solução distinta.
        """
        key = ",".join(str(position) for position in sorted(solution))
        return f"{RAW_PREFIX}{blake2b(key.encode('utf-8'), digest_size=8).hexdigest()}"

    def project(self, solution: Solution) -> Solution:
        """Projeção da solução; aqui é a identidade (sem particionamento).

        Args:
            solution: solução completa.

        Returns:
            A própria ``solution``, inalterada.
        """
        return solution

    def describe(self) -> dict:
        """Resumo serializável do esquema, para relatórios e logs.

        Returns:
            Dicionário com o nome do esquema.
        """
        return {"scheme": self.name}


class EntropyScheme:
    """Particionamento por entropia de Shannon; adaptador fino sobre :class:`Partition`."""

    name = "entropy"

    def __init__(self, partition: entropy_mod.Partition) -> None:
        self.partition = partition

    @classmethod
    def build(
        cls,
        solutions: list[Solution],
        n: int,
        percent: float | None = None,
        z: int | None = None,
        tie_break: str = "random",
        seed: int | None = None,
    ) -> "EntropyScheme":
        """Constrói o esquema a partir de ``S(T)``.

        Args:
            solutions: soluções únicas de ``S(T)``.
            n: número total de posições do espaço de busca.
            percent: critério de área ``X%``; dê exatamente um de ``percent``/``z``.
            z: número fixo de posições a reter; dê exatamente um de ``percent``/``z``.
            tie_break: política de desempate do ranking de entropia.
            seed: semente do desempate aleatório.

        Returns:
            O :class:`EntropyScheme` resultante.
        """
        return cls(
            entropy_mod.build_partition(
                solutions, n, percent=percent, z=z, tie_break=tie_break, seed=seed
            )
        )

    def assign(self, solution: Solution) -> str:
        """Id da localização em que a solução cai.

        Args:
            solution: solução completa.

        Returns:
            Id da localização.
        """
        return self.partition.assign(solution)

    def project(self, solution: Solution) -> Solution:
        """Projeção da solução sobre as posições retidas.

        Args:
            solution: solução completa.

        Returns:
            A solução restrita às posições retidas.
        """
        return self.partition.project(solution)

    def describe(self) -> dict:
        """Resumo serializável do particionamento subjacente.

        Returns:
            Dicionário com as estatísticas do particionamento.
        """
        return self.partition.describe()


def build_scheme(
    name: str,
    solutions: list[Solution],
    n: int,
    percent: float | None = None,
    z: int | None = None,
    tie_break: str = "random",
    seed: int | None = None,
):
    """Constrói um esquema de particionamento pelo nome.

    Args:
        name: ``"raw"`` ou ``"entropy"``.
        solutions: soluções únicas de ``S(T)``.
        n: número total de posições do espaço de busca.
        percent: critério de área ``X%`` (só para ``"entropy"``).
        z: número fixo de posições a reter (só para ``"entropy"``).
        tie_break: política de desempate do ranking de entropia (só para
            ``"entropy"``).
        seed: semente do desempate aleatório (só para ``"entropy"``).

    Returns:
        Instância de :class:`RawScheme` ou :class:`EntropyScheme`.

    Raises:
        ValueError: se ``name`` não for um esquema conhecido.
    """
    if name == "raw":
        return RawScheme()
    if name == "entropy":
        return EntropyScheme.build(
            solutions, n, percent=percent, z=z, tie_break=tie_break, seed=seed
        )
    raise ValueError(f"unknown scheme: {name!r}")
