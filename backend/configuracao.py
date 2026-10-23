import os

from dotenv import load_dotenv

# Carrega o arquivo local de ambiente; ele permite mudar o endereço do front sem alterar o código.
load_dotenv()

# Suporta a origem do frontend em 127.0.0.1 ou localhost, como as demos do Vite usam.
ORIGENS_FRONTEND = [
    origem.strip()
    for origem in os.getenv("FRONTEND_ORIGENS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if origem.strip()
]
ORIGEM_FRONTEND = os.getenv("FRONTEND_ORIGEM") or ORIGENS_FRONTEND[0] if ORIGENS_FRONTEND else "http://127.0.0.1:5173"

# Usa SQLite como fallback para manter a aplicação funcionando mesmo sem MySQL instalado.
MYSQL_HOST = os.getenv("MYSQL_HOST") or "localhost"
MYSQL_PORT = int(os.getenv("MYSQL_PORT") or "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or "pereiratatto"
MYSQL_USER = os.getenv("MYSQL_USER") or "pereiratatto_app"
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or ""
SQLITE_PATH = os.getenv("SQLITE_PATH") or os.path.join(os.path.dirname(__file__), "pereiratatto.db")
BANCO_TIPO = os.getenv("BANCO_TIPO", "sqlite" if not os.getenv("MYSQL_HOST") else "mysql")

# Configura a autenticação por JWT usada no login e nas rotas protegidas.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "pereiratatto-secreto-demo"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"
