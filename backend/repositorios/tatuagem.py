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
                CREATE TABLE IF NOT EXISTS tatuagens (
                    id SERIAL PRIMARY KEY,
                    cliente_id INTEGER NOT NULL,
                    ideia TEXT NOT NULL,
                    local_corpo VARCHAR(120) NOT NULL,
                    etapa VARCHAR(40) NOT NULL
                )
                """
            )
            banco.commit()


def criar(dados: dict) -> dict:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO tatuagens (cliente_id, ideia, local_corpo, etapa)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (dados["cliente_id"], dados["ideia"], dados["local_corpo"], "pedida"),
            )
            tatuagem = cursor.fetchone()
            banco.commit()
            return dict(tatuagem)


def buscar_por_id(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
            tatuagem = cursor.fetchone()
            return dict(tatuagem) if tatuagem is not None else None


def listar(etapa: Optional[str] = None, cliente_id: Optional[int] = None) -> list:
    consulta = "SELECT * FROM tatuagens WHERE 1 = 1"
    parametros = []

    if etapa is not None:
        consulta += " AND etapa = %s"
        parametros.append(etapa)
    if cliente_id is not None:
        consulta += " AND cliente_id = %s"
        parametros.append(cliente_id)

    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(consulta, tuple(parametros))
            tatuagens = cursor.fetchall()
            return [dict(item) for item in tatuagens]


def atualizar_etapa(tatuagem_id: int, nova_etapa: str) -> Optional[dict]:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("UPDATE tatuagens SET etapa = %s WHERE id = %s RETURNING *", (nova_etapa, tatuagem_id))
            tatuagem = cursor.fetchone()
            banco.commit()
            return dict(tatuagem) if tatuagem is not None else None


def descartar(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
            tatuagem = cursor.fetchone()
            if tatuagem is not None:
                cursor.execute("DELETE FROM tatuagens WHERE id = %s", (tatuagem_id,))
                banco.commit()
            return dict(tatuagem) if tatuagem is not None else None
