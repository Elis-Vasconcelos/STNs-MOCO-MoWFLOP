"""Wrappers de linha de comando que rodam os scripts R do repositório (``create .R``,
``plot.R``, ``metrics.R``) sem editá-los: cada um copia o script original pra um
arquivo temporário, reescreve só as constantes de pasta/parâmetro necessárias,
confere com um diff que nada mais mudou, e roda essa cópia via ``Rscript``.
"""
