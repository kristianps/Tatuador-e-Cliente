from pydantic import BaseModel, Field


# Define os dados de entrada; Field limita campos e o Pydantic responde 422 se eles não atenderem às restrições.
class TatuagemEntrada(BaseModel):
    cliente_id: int = Field(gt=0)
    ideia: str = Field(min_length=1)
    local_corpo: str = Field(min_length=1)


# Define os dados que a API devolve ao mostrar uma tatuagem.
class TatuagemSaida(BaseModel):
    id: int
    cliente_id: int
    ideia: str
    local_corpo: str
    etapa: str
