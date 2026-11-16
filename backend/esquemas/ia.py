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


# Resumo do pedido, montado pela IA a partir da conversa e revisado pela cliente antes de enviar.
# Os limites de tamanho valem também para o que a cliente edita na tela.
class ResumoPedido(BaseModel):
    estilo: str = Field(default="", max_length=120)
    elementos: List[str] = Field(default_factory=list, max_length=8)
    significado: str = Field(default="", max_length=300)
    cores: str = Field(default="", max_length=120)
    # Perguntas que o tatuador ainda precisa fazer para desenhar.
    pendencias: List[str] = Field(default_factory=list, max_length=5)
    # Local e tamanho servem só para preencher o formulário; o pedido já tem campos próprios para eles.
    local_corpo: str = Field(default="", max_length=120)
    tamanho_cm: Optional[int] = Field(default=None, ge=1, le=100)

    @field_validator("elementos", "pendencias")
    @classmethod
    def conferir_itens(cls, valores):
        if any(len(valor) > 200 for valor in valores):
            raise ValueError("Cada item do resumo pode ter no máximo 200 caracteres.")
        return [valor.strip() for valor in valores if valor.strip()]


class ResumoPedidoEntrada(BaseModel):
    historico: List[FalaAssistente] = Field(min_length=1, max_length=30)


class SugestoesEntrada(BaseModel):
    tatuagem_id: int = Field(gt=0)


class SugestoesSaida(BaseModel):
    sugestoes: List[str]
