from contextlib import closing
from typing import Optional

import mysql.connector

import configuracao


# Abre uma conexão com o banco para manter os dados do usuário centralizados na mesma infraestrutura.
def _conectar():
    return mysql.connector.connect(
        host=configuracao.MYSQL_HOST,
        port=configuracao.MYSQL_PORT,
        user=configuracao.MYSQL_USER,
        password=configuracao.MYSQL_PASSWORD,
        database=configuracao.MYSQL_DATABASE,
        charset="utf8mb4",
    )


# Cria a tabela de usuários e mantém cada e-mail único para evitar contas duplicadas.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(120) NOT NULL,
                email VARCHAR(180) NOT NULL UNIQUE,
                senha_hash VARCHAR(255) NOT NULL,
                perfil VARCHAR(30) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        banco.commit()
        cursor.close()


# Cria os perfis padrão do sistema, com cliente e tatuador, para a aula de login funcionar no demo.
def criar_usuarios_iniciais() -> None:
    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
        total = cursor.fetchone()["total"]
        if total > 0:
            cursor.close()
            return

        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, senha_hash, perfil)
            VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)
            """,
            (
                "Bruna",
                "bruna@pereiratatto.com",
                "1ea8ab13cdfd6c5974e8fc07f2a7a4b60607531dae06191c6675775bbc8c37e8",
                "cliente",
                "Vitor",
                "vitor@pereiratatto.com",
                "7c42421deee4443932c58ff3da1b1cb7e4df04e6911bd7af56da1eeb4dd443fa",
                "tatuador",
            ),
        )
        banco.commit()
        cursor.close()


# Busca usando o e-mail para validar o login.
def buscar_por_email(email: str) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email.lower(),))
        usuario = cursor.fetchone()
        cursor.close()
        return usuario


# Busca pelo identificador para montar a sessão autenticada.
def buscar_por_id(usuario_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        cursor.close()
        return usuario
