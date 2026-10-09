from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import configuracao
from repositorios import passo as repositorio_passo
from repositorios import tatuagem as repositorio_tatuagem
from rotas import passos, tatuagens

# NOVIDADE DA AULA 08: a API está sendo inicializada com uma estrutura preparada para autenticação.
# Hoje ainda usamos escolha de perfil no frontend, mas o backend já está pronto para evoluir para
# login real, senha, hash, token JWT e rotas protegidas pelo usuário autenticado.
app = FastAPI()

# Libera requisições apenas para a origem configurada para o frontend.
# NOVIDADE DA AULA 08: em um sistema com login, aqui também se restringe quem pode acessar a API.
# No futuro, o CORS e as políticas de origem e token passam a ser parte da segurança do sistema.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[configuracao.ORIGEM_FRONTEND],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Registra as rotas de tatuagens e passos sem colocar endpoints neste arquivo.
# NOVIDADE DA AULA 08: a ideia é que cada rota possa ser acessada somente conforme o perfil/logado.
# Ou seja, cliente vê apenas as próprias tatuagens e tatuador acessa a agenda e fichas.
app.include_router(tatuagens.router)
app.include_router(passos.router)

# Prepara as tabelas ao iniciar, criando primeiro os pedidos referenciados pelo histórico.
# NOVIDADE DA AULA 08: a persistência do estado do usuário e das permissões vai além do dado bruto;
# em seguida entram senhas, registros de usuários e associação de cada ação ao perfil correto.
repositorio_tatuagem.inicializar()
repositorio_passo.inicializar()
