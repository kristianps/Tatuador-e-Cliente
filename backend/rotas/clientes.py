from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from esquemas.cliente import CadastroPresencialSaida, ClientePresencialEntrada, ClienteSaida
from servicos import cliente as servico_cliente
from servicos import usuario as servico_usuario

# APIRouter reúne as rotas de clientes; prefix coloca /clientes na frente de todas elas.
router = APIRouter(prefix="/clientes", tags=["Clientes"])

# Só o tatuador gerencia clientes: a lista tem e-mail e telefone de todas as pessoas.
SOMENTE_TATUADOR = {servico_usuario.GRUPO_TATUADOR}


# Lista as clientes do estúdio, do site e do balcão.
@router.get("", response_model=List[ClienteSaida])
def listar_clientes(
    usuario: dict = Depends(servico_usuario.requerer_perfil(SOMENTE_TATUADOR)),
):
    return servico_cliente.listar_clientes()


# Cadastra no sistema uma cliente que veio pessoalmente ao estúdio e devolve a senha provisória dela.
# Responde 201 porque cria uma conta nova.
@router.post("", response_model=CadastroPresencialSaida, status_code=status.HTTP_201_CREATED)
def cadastrar_presencial(
    dados: ClientePresencialEntrada,
    usuario: dict = Depends(servico_usuario.requerer_perfil(SOMENTE_TATUADOR)),
):
    try:
        cliente, senha_provisoria = servico_cliente.cadastrar_presencial(
            dados.nome, dados.email.lower(), dados.telefone
        )
    except ValueError as erro:
        # Mesmo tratamento do cadastro pelo site: o e-mail já tem conta.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(erro),
        ) from erro

    return {"cliente": cliente, "senha_provisoria": senha_provisoria}
