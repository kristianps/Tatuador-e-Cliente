from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import configuracao
from rotas import passos, tatuagens

# Cria a aplicação FastAPI que será iniciada pelo comando fastapi dev.
app = FastAPI()

# Libera requisições apenas para a origem configurada para o frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[configuracao.ORIGEM_FRONTEND],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Registra as rotas de tatuagens e passos sem colocar endpoints neste arquivo.
app.include_router(tatuagens.router)
app.include_router(passos.router)
