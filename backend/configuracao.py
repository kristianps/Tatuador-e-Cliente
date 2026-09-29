import os

from dotenv import load_dotenv

# Carrega o arquivo local de ambiente; ele permite mudar o endereço do front sem alterar o código.
load_dotenv()

# Usa uma única origem exata; um valor vazio no .env mantém o endereço padrão do Vite.
ORIGEM_FRONTEND = os.getenv("FRONTEND_ORIGEM") or "http://127.0.0.1:5173"
