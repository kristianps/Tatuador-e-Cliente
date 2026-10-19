import os

from dotenv import load_dotenv

# Carrega o arquivo local de ambiente; ele permite mudar o endereço do front sem alterar o código.
load_dotenv()

# Usa uma única origem exata; um valor vazio no .env mantém o endereço padrão do Vite.
ORIGEM_FRONTEND = os.getenv("FRONTEND_ORIGEM") or "http://127.0.0.1:5173"

# Lê os dados do MySQL do ambiente para manter credenciais fora do código versionado.
MYSQL_HOST = os.getenv("MYSQL_HOST") or "127.0.0.1"
MYSQL_PORT = int(os.getenv("MYSQL_PORT") or "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or "pereiratatto"
MYSQL_USER = os.getenv("MYSQL_USER") or "pereiratatto_app"
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or ""

# Configura a autenticação por JWT usada no login e nas rotas protegidas.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "pereiratatto-secreto-demo"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"
