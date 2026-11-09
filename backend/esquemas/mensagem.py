from datetime import datetime

from pydantic import BaseModel, Field


# Entrada da mensagem: só o texto. O autor e o pedido vêm do token e do caminho da rota.
class MensagemEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=1000)


# Saída de cada balão da conversa; datetime devolve a data e a hora do envio no formato ISO.
class MensagemSaida(BaseModel):
    id: int
    tatuagem_id: int
    autor_id: int
    autor_nome: str
    autor_perfil: str
    texto: str
    criada_em: datetime
