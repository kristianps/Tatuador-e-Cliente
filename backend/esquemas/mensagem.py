from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from esquemas.imagem import TAMANHO_MAXIMO_IMAGEM, conferir_imagem


# Entrada da mensagem: texto e, se quiser, uma foto. O autor e o pedido vêm do token e do caminho da rota.
# O texto pode ficar vazio quando vai só a foto; o serviço confere que pelo menos um dos dois veio.
class MensagemEntrada(BaseModel):
    texto: str = Field(default="", max_length=1000)
    imagem: Optional[str] = Field(default=None, max_length=TAMANHO_MAXIMO_IMAGEM)

    _conferir_imagem = field_validator("imagem")(conferir_imagem)


# Saída de cada balão da conversa; datetime devolve a data e a hora do envio no formato ISO.
class MensagemSaida(BaseModel):
    id: int
    tatuagem_id: int
    autor_id: int
    autor_nome: str
    autor_perfil: str
    texto: str
    imagem: Optional[str] = None
    criada_em: datetime


# Conversa com mensagens não lidas: quantas são e qual foi a última, para mostrar no aviso.
class NaoLidaSaida(BaseModel):
    tatuagem_id: int
    ideia: str
    nao_lidas: int
    ultima_id: int
    ultimo_texto: str
    ultimo_autor: str


# Até qual mensagem a pessoa leu; ge=0 recusa número negativo.
class LeituraEntrada(BaseModel):
    ate_id: int = Field(ge=0)
