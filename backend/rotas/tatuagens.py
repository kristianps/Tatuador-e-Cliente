from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

# Os esquemas Pydantic validam a entrada e documentam os campos de saída.
from esquemas.tatuagem import TatuagemEntrada, TatuagemSaida
from servicos import tatuagem as servico_tatuagem

# APIRouter agrupa as rotas deste recurso para o main.py incluí-las na aplicação.
router = APIRouter()


# Optional deixa cada filtro opcional; response_model documenta e valida os itens devolvidos.
@router.get("/tatuagens", response_model=List[TatuagemSaida])
def listar_tatuagens(etapa: Optional[str] = None, cliente_id: Optional[int] = None):
    return servico_tatuagem.listar_tatuagens(etapa, cliente_id)


# Mostra um pedido específico e sinaliza quando o identificador não existe.
@router.get("/tatuagens/{tatuagem_id}", response_model=TatuagemSaida)
def mostrar_tatuagem(tatuagem_id: int):
    tatuagem = servico_tatuagem.buscar_tatuagem(tatuagem_id)
    if tatuagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tatuagem não encontrada.",
        )
    return tatuagem


# Cria um pedido com a etapa inicial e responde com status 201 por ser um novo recurso.
@router.post(
    "/tatuagens",
    response_model=TatuagemSaida,
    status_code=status.HTTP_201_CREATED,
)
def pedir_tatuagem(dados: TatuagemEntrada):
    return servico_tatuagem.criar_tatuagem(dados.model_dump())
