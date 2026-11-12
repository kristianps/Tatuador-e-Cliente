from typing import Optional

from pydantic import BaseModel, Field, field_validator


# Define os dados de entrada; Field limita campos e o Pydantic responde 422 se eles não atenderem às restrições.
class TatuagemEntrada(BaseModel):
    cliente_id: int = Field(gt=0)
    ideia: str = Field(min_length=1)
    local_corpo: str = Field(min_length=1)
    # Tamanho aproximado em centímetros, como a cartilha pede; ge e le limitam entre 1 e 100 cm.
    tamanho_cm: int = Field(ge=1, le=100)
    # Rascunho criado com a IA, opcional. Vem como data URL; o limite evita guardar arquivos enormes.
    imagem_ia: Optional[str] = Field(default=None, max_length=3_000_000)

    # Aceita só imagens PNG, JPEG ou WebP em base64, para ninguém guardar outro tipo de conteúdo.
    @field_validator("imagem_ia")
    @classmethod
    def conferir_imagem(cls, valor):
        tipos = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
        if valor is not None and not valor.startswith(tipos):
            raise ValueError("A imagem precisa ser PNG, JPEG ou WebP.")
        return valor


# Define os dados que a API devolve ao mostrar uma tatuagem.
class TatuagemSaida(BaseModel):
    id: int
    cliente_id: int
    ideia: str
    local_corpo: str
    # Optional porque os pedidos feitos antes deste campo não têm tamanho guardado.
    tamanho_cm: Optional[int] = None
    etapa: str


# Imagem da IA de um pedido, buscada à parte por ser grande.
class ImagemTatuagemSaida(BaseModel):
    imagem: str
