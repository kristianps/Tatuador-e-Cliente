from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

# Os esquemas Pydantic validam a entrada e documentam os campos de saída.
from esquemas.tatuagem import TatuagemEntrada, TatuagemSaida
from servicos import tatuagem as servico_tatuagem
from servicos import usuario as servico_usuario

# APIRouter agrupa as rotas deste recurso para o main.py incluí-las na aplicação.
router = APIRouter()

# NOVO: define que as duas personas do projeto fazem parte do mesmo grupo de acesso total.
# O cliente e o tatuador podem usar todas as rotas essenciais do sistema.
GRUPOS_PERMITIDOS = {servico_usuario.GRUPO_CLIENTE, servico_usuario.GRUPO_TATUADOR}


# Optional deixa cada filtro opcional; response_model documenta e valida os itens devolvidos.
@router.get("/tatuagens", response_model=List[TatuagemSaida])
def listar_tatuagens(
    etapa: Optional[str] = None,
    cliente_id: Optional[int] = None,
    # NOVO: cada rota essencial exige autenticação e valida o grupo do usuário.
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    return servico_tatuagem.listar_tatuagens(etapa, cliente_id)


# Mostra um pedido específico e sinaliza quando o identificador não existe.
@router.get("/tatuagens/{tatuagem_id}", response_model=TatuagemSaida)
def mostrar_tatuagem(
    tatuagem_id: int,
    # NOVO: a rota só pode ser acessada por grupos autorizados.
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
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
def pedir_tatuagem(
    dados: TatuagemEntrada,
    # NOVO: grupo validado antes da criação do cadastro da tatuagem.
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    return servico_tatuagem.criar_tatuagem(dados.model_dump())


# Descarta um pedido e todo o histórico que pertence a ele.
@router.delete("/tatuagens/{tatuagem_id}", status_code=status.HTTP_204_NO_CONTENT)
def descartar_tatuagem(
    tatuagem_id: int,
    # NOVO: remoção também fica restrita aos grupos autorizados do projeto.
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    tatuagem = servico_tatuagem.descartar_tatuagem(tatuagem_id)
    if tatuagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tatuagem não encontrada.",
        )
    return None
