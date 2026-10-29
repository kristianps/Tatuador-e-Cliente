from contextlib import closing
import sqlite3

try:
    import mysql.connector
except Exception:  # pragma: no cover - fallback para ambiente sem MySQL
    mysql = None

import configuracao


# Abre uma conexão com MySQL para acessar o histórico dos pedidos.
def _conectar():
    if configuracao.BANCO_TIPO == "sqlite":
        conexao = sqlite3.connect(configuracao.SQLITE_PATH)
        conexao.row_factory = sqlite3.Row
        return conexao

    if mysql is None:
        conexao = sqlite3.connect(configuracao.SQLITE_PATH)
        conexao.row_factory = sqlite3.Row
        configuracao.BANCO_TIPO = "sqlite"
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


# Cria a tabela de passos associada às tatuagens existentes.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS passos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tatuagem_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    data TEXT NOT NULL,
                    observacao TEXT NOT NULL,
                    FOREIGN KEY (tatuagem_id) REFERENCES tatuagens(id) ON DELETE CASCADE
                )
                """
            )
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS passos (
                    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    tatuagem_id INT NOT NULL,
                    tipo VARCHAR(80) NOT NULL,
                    data DATE NOT NULL,
                    observacao TEXT NOT NULL,
                    CONSTRAINT fk_passos_tatuagens
                        FOREIGN KEY (tatuagem_id) REFERENCES tatuagens(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        banco.commit()
        cursor.close()


# Guarda uma etapa no histórico usando a data validada pelo esquema.
def criar(dados: dict) -> dict:
    data = dados["data"].isoformat() if hasattr(dados["data"], "isoformat") else str(dados["data"])
    if configuracao.BANCO_TIPO == "sqlite":
        with closing(_conectar()) as banco:
            cursor = banco.cursor()
            cursor.execute(
                """
                INSERT INTO passos (tatuagem_id, tipo, data, observacao)
                VALUES (?, ?, ?, ?)
                """,
                (dados["tatuagem_id"], dados["tipo"], data, dados.get("observacao", "")),
            )
            identificador = cursor.lastrowid
            banco.commit()
            cursor.execute("SELECT * FROM passos WHERE id = ?", (identificador,))
            passo = cursor.fetchone()
            cursor.close()
            return {chave: passo[chave] for chave in passo.keys()}

    with closing(_conectar()) as banco:
        cursor = banco.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO passos (tatuagem_id, tipo, data, observacao)
            VALUES (%s, %s, %s, %s)
            """,
            (
                dados["tatuagem_id"],
                dados["tipo"],
                data,
                dados.get("observacao", ""),
            ),
        )
        identificador = cursor.lastrowid
        banco.commit()
        cursor.execute("SELECT * FROM passos WHERE id = %s", (identificador,))
        passo = cursor.fetchone()
        cursor.close()
        return passo


# Lista os passos em ordem de criação para formar o histórico do pedido.
def listar_por_tatuagem(tatuagem_id: int) -> list:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        if configuracao.BANCO_TIPO == "sqlite":
            cursor.execute("SELECT * FROM passos WHERE tatuagem_id = ? ORDER BY id", (tatuagem_id,))
            passos = [{chave: item[chave] for chave in item.keys()} for item in cursor.fetchall()]
            return passos
        cursor = banco.cursor(dictionary=True)
        cursor.execute("SELECT * FROM passos WHERE tatuagem_id = %s ORDER BY id", (tatuagem_id,))
        passos = cursor.fetchall()
        cursor.close()
        return passos


# Remove os registros do histórico sem apagar a tatuagem.
def descartar_por_tatuagem(tatuagem_id: int) -> int:
    with closing(_conectar()) as banco:
        cursor = banco.cursor()
        cursor.execute("DELETE FROM passos WHERE tatuagem_id = ?", (tatuagem_id,)) if configuracao.BANCO_TIPO == "sqlite" else cursor.execute("DELETE FROM passos WHERE tatuagem_id = %s", (tatuagem_id,))
        quantidade = cursor.rowcount
        banco.commit()
        cursor.close()
        return quantidade
