from contextlib import closing
from typing import Optional

import mysql.connector

import configuracao


# Abre uma conexão com o banco configurado para o projeto.
def _conectar():
    return mysql.connector.connect(
        host=configuracao.MYSQL_HOST,
        port=configuracao.MYSQL_PORT,
        user=configuracao.MYSQL_USER,
        password=configuracao.MYSQL_PASSWORD,
        database=configuracao.MYSQL_DATABASE,
        charset="utf8mb4",
    )


# Cria a tabela de pedidos sem apagar os dados já existentes.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
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


# Grava um pedido com a etapa inicial definida pela cartilha.
def criar(dados: dict) -> dict:
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


# Procura um pedido para os serviços decidirem como agir.
def buscar_por_id(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
        tatuagem = cursor.fetchone()
        cursor.close()
        return tatuagem


# Filtra a agenda pelos critérios que a rota recebeu.
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
        cursor = banco.cursor(dictionary=True)
        cursor.execute(consulta, tuple(parametros))
        tatuagens = cursor.fetchall()
        cursor.close()
        return tatuagens


# Atualiza a etapa escolhida pelo tatuador e devolve o pedido atualizado.
def atualizar_etapa(tatuagem_id: int, nova_etapa: str) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute(
            "UPDATE tatuagens SET etapa = %s WHERE id = %s",
            (nova_etapa, tatuagem_id),
        )
        banco.commit()
        cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
        tatuagem = cursor.fetchone()
        cursor.close()
        return tatuagem


# Exclui o pedido e os passos relacionados pelo vínculo em cascata.
def descartar(tatuagem_id: int) -> Optional[dict]:
    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tatuagens WHERE id = %s", (tatuagem_id,))
        tatuagem = cursor.fetchone()
        if tatuagem is not None:
            cursor.execute("DELETE FROM tatuagens WHERE id = %s", (tatuagem_id,))
            banco.commit()
        cursor.close()
        return tatuagem
