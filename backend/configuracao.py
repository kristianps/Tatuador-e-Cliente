import os

from dotenv import load_dotenv

# Carrega o arquivo local de ambiente; ele permite mudar o endereço do front sem alterar o código.
load_dotenv()

# Suporta a origem do frontend em 127.0.0.1, localhost e também em domínio público da Vercel.
ORIGENS_FRONTEND = [
    origem.strip()
    for origem in os.getenv("FRONTEND_ORIGENS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if origem.strip()
]
ORIGEM_FRONTEND = os.getenv("FRONTEND_ORIGEM") or (ORIGENS_FRONTEND[0] if ORIGENS_FRONTEND else "http://127.0.0.1:5173")

# URL principal do PostgreSQL em produção. O backend deixa de depender de SQLite e usa o banco do Supabase/Vercel.
URL_DO_BANCO = os.getenv("URL_DO_BANCO", "").strip()

# Mantém só os campos de compatibilidade para ambientes legados; o banco principal passa a ser o PostgreSQL.
MYSQL_HOST = os.getenv("MYSQL_HOST") or "localhost"
MYSQL_PORT = int(os.getenv("MYSQL_PORT") or "5432")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or "postgres"
MYSQL_USER = os.getenv("MYSQL_USER") or "postgres"
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or ""
SQLITE_PATH = os.getenv("SQLITE_PATH") or "pereiratatto.db"
BANCO_TIPO = os.getenv("BANCO_TIPO") or "postgresql"

# Configura a autenticação por JWT usada no login e nas rotas protegidas.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "pereiratatto-secreto-demo"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"

# Dados do envio de e-mail da recuperação de senha. O padrão aponta para o SMTP do Gmail.
# SMTP é o protocolo usado para enviar e-mails; a porta 587 inicia sem criptografia e ativa o TLS em seguida.
SMTP_HOST = os.getenv("SMTP_HOST") or "smtp.gmail.com"
SMTP_PORTA = int(os.getenv("SMTP_PORTA") or "587")
SMTP_USUARIO = (os.getenv("SMTP_USUARIO") or "").strip()
# O Google exibe a senha de app com espaços; eles não fazem parte dela.
SMTP_SENHA = (os.getenv("SMTP_SENHA") or "").replace(" ", "")
EMAIL_REMETENTE = (os.getenv("EMAIL_REMETENTE") or SMTP_USUARIO).strip()

# Endereço público da tela usado no link do e-mail. Vem da configuração, e não da requisição,
# para que ninguém consiga enviar um link apontando para outro site.
URL_DO_SITE = (os.getenv("URL_DO_SITE") or "").strip().rstrip("/")
