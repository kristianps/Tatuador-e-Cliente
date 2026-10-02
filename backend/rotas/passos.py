from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from esquemas.passo import PassoEntrada, PassoSaida, RegistroPassoSaida
from servicos import passo as servico_passo

# APIRouter agrupa os caminhos de passos relacionados a tatuagens.
router = APIRouter()


# List informa que a resposta é uma coleção; Optional deixa o identificador do cliente opcional.
@router.get("/tatuagens/{tatuagem_id}/passos", response_model=List[PassoSaida])
def listar_passos(tatuagem_id: int, cliente_id: Optional[int] = None):
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
def registrar_passo(tatuagem_id: int, dados: PassoEntrada):
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
def limpar_historico(tatuagem_id: int):
    quantidade = servico_passo.limpar_historico(tatuagem_id)
    if quantidade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tatuagem não encontrada.",
        )
    return {"apagados": quantidade}
