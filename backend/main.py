from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import configuracao
from repositorios import passo as repositorio_passo
from repositorios import tatuagem as repositorio_tatuagem
from repositorios import usuario as repositorio_usuario
from rotas import passos, tatuagens, usuarios

# A API é inicializada com a estrutura necessária para autenticação por JWT e perfil de usuário.
app = FastAPI(
    title="Tatuador e Cliente API",
    openapi_tags=[
        {"name": "Tatuagens", "description": "Gestão dos pedidos de tatuagem."},
        {"name": "Passos", "description": "Histórico e andamento dos pedidos."},
        {"name": "Usuários", "description": "Login, autenticação e dados do usuário."},
    ],
)


@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "tatuador-e-cliente-api",
        "database": "configured" if configuracao.URL_DO_BANCO else "not-configured",
    }

# Libera requisições para as origens do frontend em desenvolvimento e em uso local.
origens_frontend = list(dict.fromkeys(configuracao.ORIGENS_FRONTEND + [configuracao.ORIGEM_FRONTEND]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_frontend,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Registra as rotas de tatuagens e passos sem colocar endpoints neste arquivo.
app.include_router(tatuagens.router)
app.include_router(passos.router)
app.include_router(usuarios.router)

# Inicializa apenas quando a URL do PostgreSQL estiver preenchida.
# Em desenvolvimento local o .env deve definir URL_DO_BANCO; em deploy do Vercel essa variável
# precisa ser configurada no painel do projeto, ou o app fica disponível mas sem banco.
if configuracao.URL_DO_BANCO:
    try:
        repositorio_tatuagem.inicializar()
        repositorio_passo.inicializar()
        repositorio_usuario.inicializar()
        repositorio_usuario.criar_usuarios_iniciais()
    except Exception as erro:
        print(f"Aviso de inicialização do banco: {erro}")
else:
    print("Aviso: URL_DO_BANCO não configurada. O backend iniciou sem conexão ao PostgreSQL.")
