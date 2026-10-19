from pydantic import BaseModel, EmailStr, Field


# Define os campos necessários para o login e para devolver o usuário autenticado.
class UsuarioLoginEntrada(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=4)


class UsuarioSaida(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str


class LoginResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSaida
