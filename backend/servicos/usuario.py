import hashlib
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from configuracao import JWT_ALGORITHM, JWT_SECRET_KEY
from repositorios import usuario as repositorio_usuario

security = HTTPBearer()

# NOVO: definição dos grupos do sistema. Cada persona do projeto vira um grupo.
# "cliente" e "tatuador" representam os dois papéis principais do produto.
GRUPO_CLIENTE = "cliente"
GRUPO_TATUADOR = "tatuador"

# NOVO: conjunto com os grupos que possuem acesso total ao sistema neste momento.
# Como o projeto tem duas personas e cada uma deve ter acesso completo às rotas essenciais,
# ambos os perfis são liberados para todas as operações da API principal.
GRUPOS_COM_ACESSO_TOTAL = {GRUPO_CLIENTE, GRUPO_TATUADOR}


# Usa um hash PBKDF2 para manter a senha fora do código e permitir a validação no login.
def _hash_senha(senha: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        JWT_SECRET_KEY.encode("utf-8"),
        100_000,
    ).hex()


# Verifica credenciais e devolve o usuário associado ao e-mail se a senha bater.
def autenticar_usuario(email: str, senha: str) -> Optional[dict]:
    usuario = repositorio_usuario.buscar_por_email(email)
    if usuario is None:
        return None

    if _hash_senha(senha) != usuario["senha_hash"]:
        return None

    return usuario


def cadastrar_usuario(
    nome: str, email: str, senha: str, perfil: str = GRUPO_CLIENTE
) -> dict:
    perfil_normalizado = perfil.lower().strip()
    if perfil_normalizado not in GRUPOS_COM_ACESSO_TOTAL:
        raise ValueError("Perfil inválido. Use 'cliente' ou 'tatuador'.")

    usuario = repositorio_usuario.criar_usuario(
        nome, email, senha, perfil_normalizado
    )
    if usuario is None:
        raise ValueError("Não foi possível criar o usuário.")
    return usuario


# Gera o token JWT que acompanhará as requisições autenticadas no backend.
def gerar_token(usuario: dict) -> str:
    payload = {
        "sub": str(usuario["id"]),
        "email": usuario["email"],
        "perfil": usuario["perfil"],
        "nome": usuario["nome"],
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# Descreve para o backend quem está autenticado em cada requisição protegida.
def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if credenciais is None or credenciais.credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credenciais.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro

    usuario = repositorio_usuario.buscar_por_id(int(payload["sub"]))
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


# NOVO: dependência de autorização por grupo.
# Essa função atua como um guard de acesso: primeiro valida o token e depois verifica
# se o perfil do usuário pertence ao conjunto de grupos permitidos para a rota.
def requerer_perfil(grupos_permitidos: set[str]):
    def dependencia(usuario: dict = Depends(obter_usuario_atual)) -> dict:
        perfil_usuario = usuario.get("perfil")

        # NOVO: se o perfil do usuário não estiver na lista permitida, negamos o acesso.
        # Esse bloqueio é específico do assunto de grupos de usuários, então a regra fica bem clara.
        if perfil_usuario not in grupos_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acesso negado para o perfil '{perfil_usuario}'. "
                    "Este usuário não pertence ao grupo autorizado para esta rota."
                ),
            )

        return usuario

    return dependencia
