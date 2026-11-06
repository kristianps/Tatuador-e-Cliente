from fastapi import APIRouter, Depends, HTTPException, status

from esquemas.usuario import (
    LoginResposta,
    MensagemSaida,
    RecuperacaoSenhaEntrada,
    RedefinicaoSenhaEntrada,
    UsuarioCadastroEntrada,
    UsuarioLoginEntrada,
    UsuarioSaida,
)
from servicos import usuario as servico_usuario

# APIRouter reúne as rotas de login e sessão do sistema para o main.py registrar.
router = APIRouter(tags=["Usuários"])


@router.post("/cadastro", response_model=UsuarioSaida)
def cadastrar(dados: UsuarioCadastroEntrada):
    try:
        usuario = servico_usuario.cadastrar_usuario(
            nome=dados.nome,
            email=dados.email.lower(),
            senha=dados.senha,
        )
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(erro),
        ) from erro

    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "perfil": usuario["perfil"],
    }


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


# Responde sempre o mesmo texto para ninguém descobrir quais e-mails têm conta.
@router.post("/recuperar-senha", response_model=MensagemSaida)
def recuperar_senha(dados: RecuperacaoSenhaEntrada):
    servico_usuario.solicitar_recuperacao_senha(dados.email.lower())
    return {"mensagem": "Se houver uma conta com esse e-mail, enviamos um link para criar uma nova senha."}


# Troca a senha usando o código do link; link vencido, usado ou inventado recebe a mesma resposta.
@router.post("/redefinir-senha", response_model=MensagemSaida)
def redefinir_senha(dados: RedefinicaoSenhaEntrada):
    if not servico_usuario.redefinir_senha(dados.token, dados.senha):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este link é inválido ou expirou. Peça um novo.",
        )
    return {"mensagem": "Senha alterada com sucesso."}


# Retorna o usuário autenticado para a tela confirmar a sessão em uso.
@router.get("/me", response_model=UsuarioSaida)
def mostrar_me(usuario: dict = Depends(servico_usuario.obter_usuario_atual)):
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "perfil": usuario["perfil"],
    }
