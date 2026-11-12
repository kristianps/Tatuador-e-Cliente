from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# Dados que o tatuador preenche no balcão. Não há senha: o sistema gera uma provisória.
class ClientePresencialEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    # pattern aceita só números, espaços e os sinais usados em telefone: + ( ) -
    telefone: Optional[str] = Field(default=None, max_length=30, pattern=r"^[0-9+()\- ]*$")

    # field_validator roda antes da validação do campo; aqui transforma telefone em branco em "sem telefone".
    @field_validator("telefone", mode="before")
    @classmethod
    def telefone_vazio_vira_nulo(cls, valor):
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor.strip() if isinstance(valor, str) else valor


# Cliente como aparece na lista do estúdio, com a origem do cadastro e quantos pedidos tem.
class ClienteSaida(BaseModel):
    id: int
    nome: str
    email: str
    telefone: Optional[str] = None
    origem: str
    pedidos: int


# Resposta do cadastro presencial: a cliente criada e a senha provisória, mostrada uma única vez.
class CadastroPresencialSaida(BaseModel):
    cliente: ClienteSaida
    senha_provisoria: str
