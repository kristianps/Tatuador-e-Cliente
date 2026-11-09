from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from esquemas.mensagem import MensagemEntrada, MensagemSaida
from servicos import mensagem as servico_mensagem
from servicos import usuario as servico_usuario

# APIRouter agrupa as rotas da conversa de cada pedido.
router = APIRouter(tags=["Mensagens"])

# Cliente e tatuador conversam; o serviço confere se a cliente é dona do pedido.
GRUPOS_PERMITIDOS = {servico_usuario.GRUPO_CLIENTE, servico_usuario.GRUPO_TATUADOR}


# Lista a conversa do pedido. A tela chama esta rota a cada poucos segundos com depois_de,
# o id da última mensagem que ela já mostra, para receber só as novas.
# Query(ge=0) declara um parâmetro de consulta que não aceita número negativo.
@router.get("/tatuagens/{tatuagem_id}/mensagens", response_model=List[MensagemSaida])
def listar_mensagens(
    tatuagem_id: int,
    depois_de: int = Query(default=0, ge=0),
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    mensagens = servico_mensagem.listar_mensagens(tatuagem_id, usuario, depois_de)
    if mensagens is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tatuagem não encontrada.",
        )
    return mensagens


# Envia uma mensagem na conversa do pedido e responde 201, porque cria um recurso novo.
@router.post(
    "/tatuagens/{tatuagem_id}/mensagens",
    response_model=MensagemSaida,
    status_code=status.HTTP_201_CREATED,
)
def enviar_mensagem(
    tatuagem_id: int,
    dados: MensagemEntrada,
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    mensagem, tatuagem, motivo = servico_mensagem.enviar_mensagem(tatuagem_id, usuario, dados.texto)

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

    return mensagem
