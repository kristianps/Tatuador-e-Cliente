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

# Configura a autenticação por JWT usada no login e nas rotas protegidas.
# Não há valor padrão: com uma chave escrita no código, qualquer pessoa poderia gerar um token válido.
# Gere uma com: python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET_KEY = (os.getenv("JWT_SECRET_KEY") or "").strip()
# Sem a chave, a API inicia mesmo assim (o /health mostra o problema), mas login e rotas protegidas
# respondem 503. Derrubar a API inteira deixava o site fora do ar só com um erro genérico da Vercel.
JWT_CONFIGURADA = len(JWT_SECRET_KEY) >= 32
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"
# Por quantas horas o login vale. Depois disso, a pessoa precisa entrar de novo.
JWT_HORAS_VALIDADE = int(os.getenv("JWT_HORAS_VALIDADE") or "12")

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

# Inteligência artificial. As chaves ficam só no servidor (.env e variáveis da Vercel), nunca na tela,
# porque quem tem a chave gasta em nome do estúdio.
# Google AI Studio é o serviço principal para texto; a OpenRouter fica de reserva.
GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY") or "").strip()
OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()

# Os nomes dos modelos mudam com o tempo; ficam na configuração para trocar sem mexer no código.


def _lista(nome: str, padrao: str) -> list:
    return [item.strip() for item in (os.getenv(nome) or padrao).split(",") if item.strip()]


# Vários modelos em ordem de preferência. No plano gratuito cada modelo tem a sua própria cota por minuto:
# quando um esgota (erro 429) ou está sobrecarregado (503), o próximo da lista responde no lugar.
# Para trocar, defina a variável com os nomes separados por vírgula.
GOOGLE_MODELOS_TEXTO = _lista(
    "GOOGLE_MODELOS_TEXTO",
    "gemini-3-flash-preview,gemini-3.1-flash-lite,gemini-flash-lite-latest,gemini-3.5-flash-lite",
)
OPENROUTER_MODELOS_TEXTO = _lista(
    "OPENROUTER_MODELOS_TEXTO",
    "google/gemma-4-31b-it:free,google/gemma-4-26b-a4b-it:free,nvidia/nemotron-3.5-super-vl:free",
)
# Compatibilidade: quem já tinha definido um modelo único continua com ele em primeiro lugar.
if os.getenv("GOOGLE_MODELO_TEXTO"):
    GOOGLE_MODELOS_TEXTO.insert(0, os.getenv("GOOGLE_MODELO_TEXTO").strip())
if os.getenv("OPENROUTER_MODELO_TEXTO"):
    OPENROUTER_MODELOS_TEXTO.insert(0, os.getenv("OPENROUTER_MODELO_TEXTO").strip())
