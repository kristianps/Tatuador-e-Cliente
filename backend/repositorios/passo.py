from contextlib import closing
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

import configuracao


def _conectar():
    if not configuracao.URL_DO_BANCO:
        raise RuntimeError("URL_DO_BANCO não foi configurada. Defina a variável de ambiente no projeto da Vercel.")
    return psycopg2.connect(configuracao.URL_DO_BANCO)


def inicializar() -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS passos (
                    id SERIAL PRIMARY KEY,
                    tatuagem_id INTEGER NOT NULL,
                    tipo VARCHAR(80) NOT NULL,
                    data DATE NOT NULL,
                    observacao TEXT NOT NULL,
                    CONSTRAINT fk_passos_tatuagens
                        FOREIGN KEY (tatuagem_id) REFERENCES tatuagens(id) ON DELETE CASCADE
                )
                """
            )
            banco.commit()


def criar(dados: dict) -> dict:
    data = dados["data"].isoformat() if hasattr(dados["data"], "isoformat") else str(dados["data"])
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO passos (tatuagem_id, tipo, data, observacao)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (dados["tatuagem_id"], dados["tipo"], data, dados.get("observacao", "")),
            )
            passo = cursor.fetchone()
            banco.commit()
            return dict(passo)


def listar_por_tatuagem(tatuagem_id: int) -> list:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM passos WHERE tatuagem_id = %s ORDER BY id", (tatuagem_id,))
            return [dict(item) for item in cursor.fetchall()]


def descartar_por_tatuagem(tatuagem_id: int) -> int:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute("DELETE FROM passos WHERE tatuagem_id = %s", (tatuagem_id,))
            quantidade = cursor.rowcount
            banco.commit()
            return quantidade
