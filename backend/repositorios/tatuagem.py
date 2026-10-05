import sqlite3
from contextlib import closing
from typing import Optional

import configuracao


# Abre uma conexão independente e ativa a exclusão dos dados relacionados.
def _conectar() -> sqlite3.Connection:
    banco = sqlite3.connect(configuracao.CAMINHO_BANCO)
    banco.row_factory = sqlite3.Row
    banco.execute("PRAGMA foreign_keys = ON")
    return banco


# Cria a tabela de pedidos uma vez, sem apagar os dados que já existem.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        banco.execute(
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
        banco.commit()


# Grava um pedido com a etapa inicial definida pela cartilha.
def criar(dados: dict) -> dict:
    with closing(_conectar()) as banco:
        with banco:
            cursor = banco.execute(
                """
                INSERT INTO tatuagens (cliente_id, ideia, local_corpo, etapa)
                VALUES (?, ?, ?, ?)
                """,
                (dados["cliente_id"], dados["ideia"], dados["local_corpo"], "pedida"),
            )
            tatuagem = banco.execute(
                "SELECT * FROM tatuagens WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(tatuagem)


# Procura um pedido pelo identificador para os serviços decidirem como agir.
def buscar_por_id(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        tatuagem = banco.execute(
            "SELECT * FROM tatuagens WHERE id = ?", (tatuagem_id,)
        ).fetchone()
        return dict(tatuagem) if tatuagem is not None else None


# Filtra a agenda pelos critérios que a rota recebeu.
def listar(etapa: Optional[str] = None, cliente_id: Optional[int] = None) -> list:
    consulta = "SELECT * FROM tatuagens WHERE 1 = 1"
    parametros = []

    if etapa is not None:
        consulta += " AND etapa = ?"
        parametros.append(etapa)
    if cliente_id is not None:
        consulta += " AND cliente_id = ?"
        parametros.append(cliente_id)

    with closing(_conectar()) as banco:
        tatuagens = banco.execute(consulta, parametros).fetchall()
        return [dict(tatuagem) for tatuagem in tatuagens]


# Atualiza a etapa escolhida pelo tatuador e devolve o pedido atualizado.
def atualizar_etapa(tatuagem_id: int, nova_etapa: str) -> Optional[dict]:
    with closing(_conectar()) as banco:
        with banco:
            banco.execute(
                "UPDATE tatuagens SET etapa = ? WHERE id = ?",
                (nova_etapa, tatuagem_id),
            )
            tatuagem = banco.execute(
                "SELECT * FROM tatuagens WHERE id = ?", (tatuagem_id,)
            ).fetchone()
            return dict(tatuagem) if tatuagem is not None else None


# Exclui o pedido; a chave estrangeira apaga também os passos vinculados.
def descartar(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        with banco:
            tatuagem = banco.execute(
                "SELECT * FROM tatuagens WHERE id = ?", (tatuagem_id,)
            ).fetchone()
            if tatuagem is None:
                return None

            banco.execute("DELETE FROM tatuagens WHERE id = ?", (tatuagem_id,))
            return dict(tatuagem)
