from contextlib import closing
import hashlib
import sqlite3
from typing import Optional

import mysql.connector

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


# Abre uma conexão com o banco para manter os dados do usuário centralizados na mesma infraestrutura.
def _conectar():
    if configuracao.BANCO_TIPO == "sqlite":
        conexao = sqlite3.connect(configuracao.SQLITE_PATH)
        conexao.row_factory = sqlite3.Row
        return conexao

    try:
        return mysql.connector.connect(
            host=configuracao.MYSQL_HOST,
            port=configuracao.MYSQL_PORT,
            user=configuracao.MYSQL_USER,
            password=configuracao.MYSQL_PASSWORD,
            database=configuracao.MYSQL_DATABASE,
            charset="utf8mb4",
        )
    except mysql.connector.Error:
        conexao = sqlite3.connect(configuracao.SQLITE_PATH)
        conexao.row_factory = sqlite3.Row
        configuracao.BANCO_TIPO = "sqlite"
        return conexao


# Cria a tabela de usuários e mantém cada e-mail único para evitar contas duplicadas.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    senha_hash TEXT NOT NULL,
                    perfil TEXT NOT NULL
                )
                """
            )
        else:
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
    usuarios = [
        ("Bruna", "bruna@pereiratatto.com", "bruna123", "cliente"),
        ("Vitor", "vitor@pereiratatto.com", "vitor123", "tatuador"),
    ]

    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        for nome, email, senha, perfil in usuarios:
            if configuracao.BANCO_TIPO == "sqlite":
                cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email.lower(),))
                usuario_existente = cursor.fetchone()
            else:
                cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email.lower(),))
                usuario_existente = cursor.fetchone()
            senha_hash = _hash_senha(senha)

            if usuario_existente is None:
                if configuracao.BANCO_TIPO == "sqlite":
                    cursor.execute(
                        """
                        INSERT INTO usuarios (nome, email, senha_hash, perfil)
                        VALUES (?, ?, ?, ?)
                        """,
                        (nome, email.lower(), senha_hash, perfil),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO usuarios (nome, email, senha_hash, perfil)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (nome, email.lower(), senha_hash, perfil),
                    )
            else:
                if configuracao.BANCO_TIPO == "sqlite":
                    cursor.execute(
                        """
                        UPDATE usuarios
                        SET nome = ?,
                            senha_hash = ?,
                            perfil = ?
                        WHERE email = ?
                        """,
                        (nome, senha_hash, perfil, email.lower()),
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
        cursor.close()


# Busca usando o e-mail para validar o login.
def buscar_por_email(email: str) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email.lower(),))
            usuario = cursor.fetchone()
            if usuario is None:
                return None
            return {chave: usuario[chave] for chave in usuario.keys()}

        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email.lower(),))
        usuario = cursor.fetchone()
        cursor.close()
        return usuario


# Busca pelo identificador para montar a sessão autenticada.
def buscar_por_id(usuario_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            usuario = cursor.fetchone()
            if usuario is None:
                return None
            return {chave: usuario[chave] for chave in usuario.keys()}

        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        cursor.close()
        return usuario
