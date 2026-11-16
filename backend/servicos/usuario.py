from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import secrets
import smtplib
import ssl
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from configuracao import (
    EMAIL_REMETENTE,
    JWT_ALGORITHM,
    JWT_HORAS_VALIDADE,
    SMTP_HOST,
    SMTP_PORTA,
    SMTP_SENHA,
    SMTP_USUARIO,
    URL_DO_SITE,
)
import configuracao
from repositorios import usuario as repositorio_usuario
import seguranca

security = HTTPBearer()

# O sistema permite dois perfis válidos: cliente e tatuador.
# Qualquer conta real registrada deve conseguir autenticar corretamente.
GRUPO_CLIENTE = "cliente"
GRUPO_TATUADOR = "tatuador"

# Regras da recuperação de senha: o link vence rápido e cada conta recebe poucos e-mails por hora.
MINUTOS_VALIDADE_RECUPERACAO = 30
MAXIMO_RECUPERACOES_POR_HORA = 3


# Verifica credenciais e devolve o usuário associado ao e-mail se a senha bater.
def autenticar_usuario(email: str, senha: str) -> Optional[dict]:
    _chave_jwt()
    usuario = repositorio_usuario.buscar_por_email(email)
    if usuario is None:
        return None

    if not seguranca.verificar_senha(senha, usuario["senha_hash"]):
        return None

    # Contas com o hash antigo passam para o formato novo aproveitando a senha que acabou de ser digitada.
    if seguranca.precisa_atualizar(usuario["senha_hash"]):
        repositorio_usuario.atualizar_senha_hash(usuario["id"], seguranca.gerar_hash_senha(senha))

    return usuario


# Todo cadastro público cria uma conta de cliente, sem aceitar outro perfil vindo da requisição.
def cadastrar_usuario(nome: str, email: str, senha: str) -> dict:
    usuario = repositorio_usuario.criar_usuario(nome, email, senha, GRUPO_CLIENTE)
    if usuario is None:
        raise ValueError("Não foi possível criar o usuário.")
    return usuario


# Guarda só o resumo do código: quem ler o banco não consegue montar um link válido.
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# Monta e envia o e-mail. O código vai depois do # porque essa parte da URL não chega aos servidores nem aos logs.
def _enviar_email_recuperacao(usuario: dict, token: str) -> None:
    mensagem = EmailMessage()
    mensagem["Subject"] = "Recuperação de senha - PereiraTatto"
    mensagem["From"] = EMAIL_REMETENTE
    mensagem["To"] = usuario["email"]
    mensagem.set_content(
        f"Olá, {usuario['nome']}!\n\n"
        "Recebemos um pedido para criar uma nova senha na PereiraTatto.\n"
        "Abra o link abaixo para continuar:\n\n"
        f"{URL_DO_SITE}/#redefinir-senha={token}\n\n"
        f"O link vale por {MINUTOS_VALIDADE_RECUPERACAO} minutos e só pode ser usado uma vez.\n"
        "Se não foi você, ignore este e-mail: sua senha continua a mesma.\n"
    )

    # O timeout evita que a requisição fique presa se o servidor de e-mail não responder.
    with smtplib.SMTP(SMTP_HOST, SMTP_PORTA, timeout=10) as servidor:
        # starttls ativa a criptografia antes de enviar a senha do e-mail.
        servidor.starttls(context=ssl.create_default_context())
        servidor.login(SMTP_USUARIO, SMTP_SENHA)
        servidor.send_message(mensagem)


# Cria o pedido e envia o link. Não devolve nada para a rota responder igual, exista a conta ou não.
def solicitar_recuperacao_senha(email: str) -> None:
    usuario = repositorio_usuario.buscar_por_email(email)
    if usuario is None:
        return

    if not (SMTP_USUARIO and SMTP_SENHA and EMAIL_REMETENTE and URL_DO_SITE):
        print("Aviso: envio de e-mail não configurado. Defina SMTP_USUARIO, SMTP_SENHA e URL_DO_SITE.")
        return

    if repositorio_usuario.contar_recuperacoes_recentes(usuario["id"]) >= MAXIMO_RECUPERACOES_POR_HORA:
        return

    # secrets gera um código imprevisível, próprio para segurança; o módulo random não serve para isso.
    token = secrets.token_urlsafe(32)
    repositorio_usuario.criar_recuperacao(
        usuario["id"], _hash_token(token), MINUTOS_VALIDADE_RECUPERACAO
    )

    # A falha fica só no log da Vercel, para a resposta não revelar que a conta existe.
    try:
        _enviar_email_recuperacao(usuario, token)
    except (OSError, smtplib.SMTPException) as erro:
        print(f"Aviso: falha ao enviar o e-mail de recuperação: {type(erro).__name__}")


# Devolve True quando a senha mudou; a rota escolhe o status com base nesse resultado.
def redefinir_senha(token: str, senha: str) -> bool:
    return repositorio_usuario.redefinir_senha_por_token(_hash_token(token), seguranca.gerar_hash_senha(senha))


# Devolve a chave do JWT ou recusa com 503 (serviço indisponível) quando ela não foi configurada.
# Fica numa função, e não num if na importação, para o resto da API continuar no ar sem a chave.
def _chave_jwt() -> str:
    if not configuracao.JWT_CONFIGURADA:
        print("Aviso: JWT_SECRET_KEY ausente ou curta demais; login e rotas protegidas estão desativados.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login indisponível: o servidor está sem a JWT_SECRET_KEY configurada.",
        )
    return configuracao.JWT_SECRET_KEY


# Gera o token JWT que acompanhará as requisições autenticadas no backend.
def gerar_token(usuario: dict) -> str:
    payload = {
        "sub": str(usuario["id"]),
        "email": usuario["email"],
        "perfil": usuario["perfil"],
        "nome": usuario["nome"],
        # exp é a data de validade; o jwt.decode recusa sozinho os tokens vencidos.
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_HORAS_VALIDADE),
    }
    return jwt.encode(payload, _chave_jwt(), algorithm=JWT_ALGORITHM)


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
    chave = _chave_jwt()
    try:
        payload = jwt.decode(token, chave, algorithms=[JWT_ALGORITHM])
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
