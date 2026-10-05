import sqlite3
from contextlib import closing

import configuracao


# Abre uma conexão com a chave estrangeira ligada para manter o histórico associado.
def _conectar() -> sqlite3.Connection:
    banco = sqlite3.connect(configuracao.CAMINHO_BANCO)
    banco.row_factory = sqlite3.Row
    banco.execute("PRAGMA foreign_keys = ON")
    return banco


# Cria a tabela de passos ligada aos pedidos existentes.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        banco.execute(
            """
            CREATE TABLE IF NOT EXISTS passos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tatuagem_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                data TEXT NOT NULL,
                observacao TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (tatuagem_id) REFERENCES tatuagens(id) ON DELETE CASCADE
            )
            """
        )
        banco.commit()


# Guarda a etapa no histórico usando uma data no formato ISO.
def criar(dados: dict) -> dict:
    data = dados["data"].isoformat() if hasattr(dados["data"], "isoformat") else str(dados["data"])
    with closing(_conectar()) as banco:
        with banco:
            cursor = banco.execute(
                """
                INSERT INTO passos (tatuagem_id, tipo, data, observacao)
                VALUES (?, ?, ?, ?)
                """,
                (
                    dados["tatuagem_id"],
                    dados["tipo"],
                    data,
                    dados.get("observacao", ""),
                ),
            )
            passo = banco.execute(
                "SELECT * FROM passos WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(passo)


# Lista os passos em ordem de criação para formar o histórico do pedido.
def listar_por_tatuagem(tatuagem_id: int) -> list:
    with closing(_conectar()) as banco:
        passos = banco.execute(
            "SELECT * FROM passos WHERE tatuagem_id = ? ORDER BY id",
            (tatuagem_id,),
        ).fetchall()
        return [dict(passo) for passo in passos]


# Remove os registros de um histórico sem alterar o pedido.
def descartar_por_tatuagem(tatuagem_id: int) -> int:
    with closing(_conectar()) as banco:
        with banco:
            cursor = banco.execute(
                "DELETE FROM passos WHERE tatuagem_id = ?", (tatuagem_id,)
            )
            return cursor.rowcount
