from pydantic import BaseModel, EmailStr, Field


# Define os campos necessários para o login e para devolver o usuário autenticado.
class UsuarioLoginEntrada(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=4)


# O perfil não faz parte da entrada: quem define o perfil de uma conta nova é o backend.
class UsuarioCadastroEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=100)


class UsuarioSaida(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str


class LoginResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSaida
