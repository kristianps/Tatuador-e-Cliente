from contextlib import closing
import sqlite3
from typing import Optional

import mysql.connector

import configuracao


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


def inicializar() -> None:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tatuagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    ideia TEXT NOT NULL,
                    local_corpo TEXT NOT NULL,
                    etapa TEXT NOT NULL
                )
                """
            )
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tatuagens (
                    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    cliente_id INT NOT NULL,
                    ideia TEXT NOT NULL,
                    local_corpo VARCHAR(120) NOT NULL,
                    etapa VARCHAR(40) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        banco.commit()
        cursor.close()


def criar(dados: dict) -> dict:
    if configuracao.BANCO_TIPO == "sqlite":
        with closing(_conectar()) as banco:
            cursor = banco.cursor()
            cursor.execute(
                """
                INSERT INTO tatuagens (cliente_id, ideia, local_corpo, etapa)
                VALUES (?, ?, ?, ?)
                """,
                (dados["cliente_id"], dados["ideia"], dados["local_corpo"], "pedida"),
            )
            identificador = cursor.lastrowid
            banco.commit()
            cursor.execute("SELECT * FROM tatuagens WHERE id = ?", (identificador,))
            tatuagem = cursor.fetchone()
            cursor.close()
            return {chave: tatuagem[chave] for chave in tatuagem.keys()}

    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO tatuagens (cliente_id, ideia, local_corpo, etapa)
            VALUES (%s, %s, %s, %s)
            """,
            (dados["cliente_id"], dados["ideia"], dados["local_corpo"], "pedida"),
        )
        identificador = cursor.lastrowid
        banco.commit()
        cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (identificador,))
        tatuagem = cursor.fetchone()
        cursor.close()
        return tatuagem


def buscar_por_id(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute("SELECT * FROM tatuagens WHERE id = ?", (tatuagem_id,))
            tatuagem = cursor.fetchone()
            return {chave: tatuagem[chave] for chave in tatuagem.keys()} if tatuagem is not None else None
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
        tatuagem = cursor.fetchone()
        cursor.close()
        return tatuagem


def listar(etapa: Optional[str] = None, cliente_id: Optional[int] = None) -> list:
    consulta = "SELECT * FROM tatuagens WHERE 1 = 1"
    parametros = []

    if etapa is not None:
        consulta += " AND etapa = ?" if configuracao.BANCO_TIPO == "sqlite" else " AND etapa = %s"
        parametros.append(etapa)
    if cliente_id is not None:
        consulta += " AND cliente_id = ?" if configuracao.BANCO_TIPO == "sqlite" else " AND cliente_id = %s"
        parametros.append(cliente_id)

    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            resultado = cursor.execute(consulta, tuple(parametros)).fetchall()
            return [{chave: item[chave] for chave in item.keys()} for item in resultado]
        cursor = banco.cursor(dictionary=True)
        cursor.execute(consulta, tuple(parametros))
        tatuagens = cursor.fetchall()
        cursor.close()
        return tatuagens


def atualizar_etapa(tatuagem_id: int, nova_etapa: str) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute("UPDATE tatuagens SET etapa = ? WHERE id = ?", (nova_etapa, tatuagem_id))
            banco.commit()
            cursor.execute("SELECT * FROM tatuagens WHERE id = ?", (tatuagem_id,))
            tatuagem = cursor.fetchone()
            return {chave: tatuagem[chave] for chave in tatuagem.keys()} if tatuagem is not None else None
        cursor = banco.cursor(dictionary=True)
        cursor.execute("UPDATE tatuagens SET etapa = %s WHERE id = %s", (nova_etapa, tatuagem_id))
        banco.commit()
        cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
        tatuagem = cursor.fetchone()
        cursor.close()
        return tatuagem


def descartar(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute("SELECT * FROM tatuagens WHERE id = ?", (tatuagem_id,))
            tatuagem = cursor.fetchone()
            if tatuagem is not None:
                cursor.execute("DELETE FROM tatuagens WHERE id = ?", (tatuagem_id,))
                banco.commit()
            return {chave: tatuagem[chave] for chave in tatuagem.keys()} if tatuagem is not None else None
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
        tatuagem = cursor.fetchone()
        if tatuagem is not None:
            cursor.execute("DELETE FROM tatuagens WHERE id = %s", (tatuagem_id,))
            banco.commit()
        cursor.close()
        return tatuagem
