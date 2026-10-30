from contextlib import closing
import hashlib

import psycopg2
from psycopg2.extras import RealDictCursor

import configuracao


# Mantém o mesmo algoritmo de hash usado em servicos.usuario para que as credenciais demo
# continuem válidas mesmo após reinicializar o banco ou os usuários iniciais.
def _hash_senha(senha: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        configuracao.JWT_SECRET_KEY.encode("utf-8"),
        100_000,
    ).hex()


def _conectar():
    if not configuracao.URL_DO_BANCO:
        raise RuntimeError("URL_DO_BANCO não foi configurada. Defina a variável de ambiente no projeto da Vercel.")
    return psycopg2.connect(configuracao.URL_DO_BANCO)


# Cria a tabela de usuários e mantém cada e-mail único para evitar contas duplicadas.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(120) NOT NULL,
                    email VARCHAR(180) NOT NULL UNIQUE,
                    senha_hash VARCHAR(255) NOT NULL,
                    perfil VARCHAR(30) NOT NULL
                )
                """
            )
            banco.commit()


# Cria os perfis padrão do sistema, com cliente e tatuador, para a aula de login funcionar no demo.
def criar_usuarios_iniciais() -> None:
    usuarios = [
        ("Bruna", "bruna@pereiratatto.com", "bruna123", "cliente"),
        ("Vitor", "vitor@pereiratatto.com", "vitor123", "tatuador"),
    ]

    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            for nome, email, senha, perfil in usuarios:
                senha_hash = _hash_senha(senha)
                cursor.execute(
                    "SELECT * FROM usuarios WHERE email = %s",
                    (email.lower(),),
                )
                usuario_existente = cursor.fetchone()

                if usuario_existente is None:
                    cursor.execute(
                        """
                        INSERT INTO usuarios (nome, email, senha_hash, perfil)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (nome, email.lower(), senha_hash, perfil),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE usuarios
                        SET nome = %s,
                            senha_hash = %s,
                            perfil = %s
                        WHERE email = %s
                        """,
                        (nome, senha_hash, perfil, email.lower()),
                    )
            banco.commit()


# Busca usando o e-mail para validar o login.
def buscar_por_email(email: str):
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email.lower(),))
            usuario = cursor.fetchone()
            return dict(usuario) if usuario is not None else None


# Busca pelo identificador para montar a sessão autenticada.
def buscar_por_id(usuario_id: int):
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()
            return dict(usuario) if usuario is not None else None


# Cria uma nova conta para o sistema e retorna o usuário salvo.
def criar_usuario(nome: str, email: str, senha: str, perfil: str = "cliente"):
    email_normalizado = email.lower().strip()
    senha_hash = _hash_senha(senha)

    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = %s",
                (email_normalizado,),
            )
            if cursor.fetchone() is not None:
                raise ValueError("Já existe uma conta cadastrada com este e-mail.")

            cursor.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash, perfil)
                VALUES (%s, %s, %s, %s)
                RETURNING id, nome, email, perfil
                """,
                (nome.strip(), email_normalizado, senha_hash, perfil.lower()),
            )
            usuario = cursor.fetchone()
            banco.commit()
            return dict(usuario)
