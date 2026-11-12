import secrets
from typing import Optional, Tuple

from repositorios import usuario as repositorio_usuario
from servicos.usuario import GRUPO_CLIENTE

# Letras e números sem os que se confundem ao ler em voz alta ou no papel (0/O, 1/I/L).
ALFABETO_SENHA = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
TAMANHO_SENHA_PROVISORIA = 8


# Gera a senha que o estúdio entrega à cliente no balcão.
# secrets escolhe cada caractere de forma imprevisível, própria para senhas; random não serve para isso.
def _gerar_senha_provisoria() -> str:
    return "".join(secrets.choice(ALFABETO_SENHA) for _ in range(TAMANHO_SENHA_PROVISORIA))


# Lista as clientes do estúdio, vindas do site ou do balcão, para a aba Clientes do tatuador.
def listar_clientes() -> list:
    return repositorio_usuario.listar_clientes()


# Cria a conta de uma cliente que veio pessoalmente. A conta é sempre de cliente e marcada como presencial.
# Devolve a cliente e a senha provisória; a senha só existe aqui, porque o banco guarda apenas o hash dela.
# Se o e-mail já tiver conta, o repositório levanta ValueError e a rota responde 400, como no cadastro pelo site.
def cadastrar_presencial(nome: str, email: str, telefone: Optional[str]) -> Tuple[dict, str]:
    senha_provisoria = _gerar_senha_provisoria()
    cliente = repositorio_usuario.criar_usuario(
        nome,
        email,
        senha_provisoria,
        perfil=GRUPO_CLIENTE,
        telefone=telefone,
        origem="presencial",
    )
    return {**cliente, "pedidos": 0}, senha_provisoria
