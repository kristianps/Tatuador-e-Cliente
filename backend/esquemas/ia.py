from typing import List, Literal

from pydantic import BaseModel, Field


# Uma fala da conversa com a assistente. Literal aceita só os dois valores listados.
class FalaAssistente(BaseModel):
    papel: Literal["cliente", "assistente"]
    texto: str = Field(min_length=1, max_length=1500)


# A tela manda a conversa inteira a cada pergunta, porque a IA não guarda memória entre uma chamada e outra.
# A última fala precisa ser da cliente: é a pergunta que a assistente vai responder.
class ConversaAssistenteEntrada(BaseModel):
    historico: List[FalaAssistente] = Field(min_length=1, max_length=30)


class RespostaAssistenteSaida(BaseModel):
    resposta: str


# A imagem é gerada a partir da mesma conversa.
class ImagemEntrada(BaseModel):
    historico: List[FalaAssistente] = Field(min_length=1, max_length=30)


# A imagem volta como data URL, pronta para a tela mostrar num <img>.
class ImagemSaida(BaseModel):
    imagem: str


class SugestoesEntrada(BaseModel):
    tatuagem_id: int = Field(gt=0)


class SugestoesSaida(BaseModel):
    sugestoes: List[str]
