from datetime import date

from pydantic import BaseModel, Field


# Define os dados enviados; o tipo date converte a data ISO recebida em uma data validada.
class PassoEntrada(BaseModel):
    tipo: str = Field(min_length=1)
    data: date
    observacao: str = ""


# Define os dados que a API devolve para cada passo do histórico.
class PassoSaida(BaseModel):
    id: int
    tatuagem_id: int
    tipo: str
    data: date
    observacao: str


# Reúne o passo aceito e a etapa resultante para atualizar a ficha na tela.
class RegistroPassoSaida(PassoSaida):
    etapa_atualizada: str
