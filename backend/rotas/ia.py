from fastapi import APIRouter, Depends, HTTPException, status

from esquemas.ia import (
    ConversaAssistenteEntrada,
    ImagemEntrada,
    ImagemSaida,
    RespostaAssistenteSaida,
    SugestoesEntrada,
    SugestoesSaida,
)
from servicos import ia as servico_ia
from servicos import usuario as servico_usuario

# APIRouter reúne as rotas de inteligência artificial; prefix coloca /ia na frente de todas.
router = APIRouter(prefix="/ia", tags=["Inteligência artificial"])

GRUPOS_PERMITIDOS = {servico_usuario.GRUPO_CLIENTE, servico_usuario.GRUPO_TATUADOR}


# Transforma o motivo de recusa do serviço em resposta HTTP.
# 429 (muitas requisições) para o limite diário; 503 (serviço indisponível) quando a IA não respondeu.
def _recusar(motivo: str):
    codigo = status.HTTP_429_TOO_MANY_REQUESTS if "limite" in motivo else status.HTTP_503_SERVICE_UNAVAILABLE
    raise HTTPException(status_code=codigo, detail=motivo)


# Responde a próxima fala da assistente de ideias.
@router.post("/assistente", response_model=RespostaAssistenteSaida)
def conversar(
    dados: ConversaAssistenteEntrada,
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    if dados.historico[-1].papel != "cliente":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A última fala precisa ser da cliente.")

    resposta, motivo = servico_ia.conversar(usuario, [fala.model_dump() for fala in dados.historico])
    if motivo:
        _recusar(motivo)
    return {"resposta": resposta}


# Gera o rascunho da tatuagem a partir da conversa com a assistente.
@router.post("/imagem", response_model=ImagemSaida)
def gerar_imagem(
    dados: ImagemEntrada,
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    if not any(fala.papel == "cliente" and fala.texto.strip() for fala in dados.historico):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Conte sua ideia antes de gerar a imagem.")

    imagem, motivo = servico_ia.gerar_imagem(usuario, [fala.model_dump() for fala in dados.historico])
    if motivo:
        _recusar(motivo)
    return {"imagem": imagem}


# Sugere 3 respostas prontas para a conversa de um pedido.
@router.post("/sugestoes-resposta", response_model=SugestoesSaida)
def sugerir_respostas(
    dados: SugestoesEntrada,
    usuario: dict = Depends(servico_usuario.requerer_perfil(GRUPOS_PERMITIDOS)),
):
    sugestoes, encontrada, motivo = servico_ia.sugerir_respostas(usuario, dados.tatuagem_id)
    if not encontrada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tatuagem não encontrada.")
    if motivo:
        _recusar(motivo)
    return {"sugestoes": sugestoes}
