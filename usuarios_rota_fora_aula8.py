from fastapi import APIRouter, Depends, HTTPException, status

from esquemas.usuario import LoginResposta, UsuarioLoginEntrada, UsuarioSaida
from servicos import usuario as servico_usuario

# APIRouter reúne as rotas de login e sessão do sistema para o main.py registrar.
router = APIRouter()


# Autentica usuário com e-mail e senha e devolve um token para as próximas requisições.
@router.post("/login", response_model=LoginResposta)
def login(dados: UsuarioLoginEntrada):
    usuario = servico_usuario.autenticar_usuario(dados.email.lower(), dados.senha)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    token = servico_usuario.gerar_token(usuario)
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario["perfil"],
        },
    }


# Retorna o usuário autenticado para a tela confirmar a sessão em uso.
@router.get("/me", response_model=UsuarioSaida)
def mostrar_me(usuario: dict = Depends(servico_usuario.obter_usuario_atual)):
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "perfil": usuario["perfil"],
    }
