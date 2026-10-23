from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from esquemas.passo import PassoEntrada, PassoSaida, RegistroPassoSaida
from servicos import passo as servico_passo
from servicos import usuario as servico_usuario

# APIRouter agrupa os caminhos de passos relacionados a tatuagens.
router = APIRouter(tags=["Passos"])

# NOVO: um grupo é a coleção de perfis autorizados para uma determinada área do sistema.
# Neste projeto, cliente e tatuador têm acesso total aos fluxos de tatuagem e histórico.
GRUPOS_PERMITIDOS = {servico_usuario.GRUPO_CLIENTE, servico_usuario.GRUPO_TATUADOR}


# List informa que a resposta é uma coleção; Optional deixa o identificador do cliente opcional.
@router.get("/tatuagens/{tatuagem_id}/passos", response_model=List[PassoSaida])
def listar_passos(
    tatuagem_id: int,
    cliente_id: Optional[int] = None,
    # NOVO: valida o token e depois confirma que o perfil pertence ao grupo permitido.
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    passos = servico_passo.listar_passos(tatuagem_id, cliente_id)
    if passos is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tatuagem não encontrada.",
        )
    return passos


# Registra um passo; HTTPException transforma a recusa ou ausência em uma resposta HTTP adequada.
@router.post(
    "/tatuagens/{tatuagem_id}/passos",
    response_model=RegistroPassoSaida,
    status_code=status.HTTP_201_CREATED,
)
def registrar_passo(
    tatuagem_id: int,
    dados: PassoEntrada,
    # NOVO: qualquer pessoa do grupo autorizado pode registrar etapas do andamento da tatuagem.
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    passo, tatuagem, motivo = servico_passo.registrar_passo(
        tatuagem_id, dados.model_dump()
    )

    if tatuagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tatuagem não encontrada.",
        )

    if motivo is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=motivo,
        )

    return passo


# Exclui os passos sem apagar o pedido que aparece na agenda.
@router.delete("/tatuagens/{tatuagem_id}/passos")
def limpar_historico(
    tatuagem_id: int,
    # NOVO: a exclusão do histórico também exige grupo autorizado, reforçando o controle de acesso.
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    quantidade = servico_passo.limpar_historico(tatuagem_id)
    if quantidade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tatuagem não encontrada.",
        )
    return {"apagados": quantidade}
