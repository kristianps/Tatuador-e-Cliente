from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from esquemas.imagem import TAMANHO_MAXIMO_IMAGEM, conferir_imagem


# Uma fala da conversa com a assistente. Literal aceita só os dois valores listados.
# A fala da cliente pode trazer uma foto (referência, desenho ou local do corpo) para a IA analisar.
class FalaAssistente(BaseModel):
    papel: Literal["cliente", "assistente"]
    texto: str = Field(default="", max_length=1500)
    imagem: Optional[str] = Field(default=None, max_length=TAMANHO_MAXIMO_IMAGEM)

    _conferir_imagem = field_validator("imagem")(conferir_imagem)

    # model_validator roda depois de todos os campos: confere o conjunto, e não um campo só.
    @model_validator(mode="after")
    def conferir_conteudo(self):
        if not self.texto.strip() and not self.imagem:
            raise ValueError("Cada fala precisa ter texto ou foto.")
        if self.imagem and self.papel != "cliente":
            raise ValueError("Só a cliente envia fotos.")
        return self


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
