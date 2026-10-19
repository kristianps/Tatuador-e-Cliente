import hashlib
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from configuracao import JWT_ALGORITHM, JWT_SECRET_KEY
from repositorios import usuario as repositorio_usuario

security = HTTPBearer()


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
