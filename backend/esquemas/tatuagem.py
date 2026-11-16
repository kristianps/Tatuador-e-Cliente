from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from esquemas.ia import ResumoPedido


# Define os dados de entrada; Field limita campos e o Pydantic responde 422 se eles não atenderem às restrições.
class TatuagemEntrada(BaseModel):
    cliente_id: int = Field(gt=0)
    ideia: str = Field(min_length=1)
    local_corpo: str = Field(min_length=1)
    # Tamanho aproximado em centímetros, como a cartilha pede; ge e le limitam entre 1 e 100 cm.
    tamanho_cm: int = Field(ge=1, le=100)
    # Rascunho criado com a IA, opcional. Vem como data URL; o limite evita guardar arquivos enormes.
    imagem_ia: Optional[str] = Field(default=None, max_length=3_000_000)
    imagens_ia: List[str] = Field(default_factory=list, max_length=3)
    # Resumo da conversa com a assistente, já revisado pela cliente. Opcional.
    resumo_ia: Optional[ResumoPedido] = None

    # Aceita só imagens PNG, JPEG ou WebP em base64, para ninguém guardar outro tipo de conteúdo.
    @field_validator("imagem_ia")
    @classmethod
    def conferir_imagem(cls, valor):
        tipos = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
        if valor is not None and not valor.startswith(tipos):
            raise ValueError("A imagem precisa ser PNG, JPEG ou WebP.")
        return valor

    @field_validator("imagens_ia")
    @classmethod
    def conferir_imagens_ia(cls, valores):
        tipos = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
        if any(len(valor) > 3_000_000 or not valor.startswith(tipos) for valor in valores):
            raise ValueError("Cada proposta precisa ser uma imagem PNG, JPEG ou WebP de até 3 MB.")
        return valores


# Define os dados que a API devolve ao mostrar uma tatuagem.
class TatuagemSaida(BaseModel):
    id: int
    cliente_id: int
    ideia: str
    local_corpo: str
    # Optional porque os pedidos feitos antes deste campo não têm tamanho guardado.
    tamanho_cm: Optional[int] = None
    etapa: str
    # Pedidos feitos sem a assistente não têm resumo.
    resumo_ia: Optional[ResumoPedido] = None


# Imagem da IA de um pedido, buscada à parte por ser grande.
class ImagemTatuagemSaida(BaseModel):
    imagem: str


class PropostasImagemTatuagemSaida(BaseModel):
    imagens: List[str]
