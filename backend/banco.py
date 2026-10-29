import os

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# Lê a string de conexão em uma única variável de ambiente para facilitar a troca de banco
# sem espalhar host, porta, usuário, senha e nome do banco em várias chaves diferentes.
URL_DO_BANCO = os.getenv("URL_DO_BANCO", "")

# Usa NullPool porque a API será publicada na Vercel, que roda em ambiente serverless.
# Esse tipo de pool evita manter conexões ociosas abertas entre requisições e reduz o risco
# de ficar com conexões mortas ou excedendo o limite do provedor do banco.
engine = create_engine(
    URL_DO_BANCO,
    poolclass=NullPool,
)
