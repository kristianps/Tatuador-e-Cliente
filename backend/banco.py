import os

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# Lê a string de conexão em uma única variável de ambiente para facilitar a troca de banco
# sem espalhar host, porta, usuário, senha e nome do banco em várias chaves diferentes.
URL_DO_BANCO = os.getenv("URL_DO_BANCO")

# Em produção, a Vercel só cria o engine quando a variável de ambiente existir.
# Quando ela ainda não foi preenchida, a importação não deve quebrar o app inteiro;
# o backend deve informar a falha de forma clara na hora do uso da conexão.
if URL_DO_BANCO:
    # Usa NullPool porque a API será publicada na Vercel, que roda em ambiente serverless.
    # Esse tipo de pool evita manter conexões ociosas abertas entre requisições e reduz o risco
    # de ficar com conexões mortas ou excedendo o limite do provedor do banco.
    engine = create_engine(
        URL_DO_BANCO,
        poolclass=NullPool,
    )
else:
    engine = None


def get_engine():
    """Retorna o engine do banco somente quando a URL estiver configurada."""
    if engine is None:
        raise RuntimeError(
            "URL_DO_BANCO não foi configurada. Defina a variável de ambiente no projeto da Vercel."
        )
    return engine
