"""Particionamento do espaço de busca para as STNs do MoWFLOP.

Este pacote é um estágio *upstream*: lê os logs de trajetória brutos produzidos
pela campanha em C++, mapeia cada solução logada para uma *localização* de um
espaço de busca particionado, e escreve arquivos exatamente no formato que
``scripts/create .R`` já lê.  Nenhum script R é modificado, então os modelos
particionado e não particionado atravessam código R byte a byte idêntico, e
qualquer diferença nas métricas é atribuível só ao particionamento.

Esquemas implementados aqui:

``entropy``
    Particionamento por entropia de Shannon de Ochoa, Malan & Blum (Applied
    Soft Computing, 2021), Seção 5.4.

``raw``
    Sem particionamento (Ochoa et al. 2023): uma localização por solução
    distinta.  A função identidade, mantida porque é o denominador de toda
    afirmação do tipo "houve agregação, de fato?".
"""

__all__ = [
    "io_raw",
    "schemes",
    "reference_front",
    "emit",
]
