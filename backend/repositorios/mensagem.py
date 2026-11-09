from contextlib import closing

import psycopg2
from psycopg2.extras import RealDictCursor

import configuracao


# Abre uma conexão nova a cada uso, no mesmo padrão dos outros repositórios (a Vercel não guarda conexões).
def _conectar():
    if not configuracao.URL_DO_BANCO:
        raise RuntimeError("URL_DO_BANCO não foi configurada. Defina a variável de ambiente no projeto da Vercel.")
    return psycopg2.connect(configuracao.URL_DO_BANCO)


# Cria a tabela da conversa de cada pedido, se ela ainda não existir.
# ON DELETE CASCADE apaga as mensagens junto quando o pedido ou o usuário é descartado.
# TIMESTAMPTZ guarda data, hora e fuso; DEFAULT NOW() preenche o horário do envio sozinho.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS mensagens (
                    id SERIAL PRIMARY KEY,
                    tatuagem_id INTEGER NOT NULL,
                    autor_id INTEGER NOT NULL,
                    texto TEXT NOT NULL,
                    criada_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_mensagens_tatuagens
                        FOREIGN KEY (tatuagem_id) REFERENCES tatuagens(id) ON DELETE CASCADE,
                    CONSTRAINT fk_mensagens_usuarios
                        FOREIGN KEY (autor_id) REFERENCES usuarios(id) ON DELETE CASCADE
                )
                """
            )
            banco.commit()


# Grava a mensagem e já devolve o nome e o perfil de quem escreveu, para a tela montar o balão.
# O WITH (CTE) guarda a linha recém-inserida com um nome, e o SELECT seguinte a junta com o usuário.
def criar(tatuagem_id: int, autor_id: int, texto: str) -> dict:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH nova AS (
                    INSERT INTO mensagens (tatuagem_id, autor_id, texto)
                    VALUES (%s, %s, %s)
                    RETURNING *
                )
                SELECT nova.*, usuarios.nome AS autor_nome, usuarios.perfil AS autor_perfil
                FROM nova
                JOIN usuarios ON usuarios.id = nova.autor_id
                """,
                (tatuagem_id, autor_id, texto),
            )
            mensagem = cursor.fetchone()
            banco.commit()
            return dict(mensagem)


# Lista a conversa de um pedido em ordem de envio.
# depois_de traz só as mensagens com id maior que o último que a tela já tem,
# assim a consulta repetida a cada poucos segundos devolve apenas o que é novo.
def listar_por_tatuagem(tatuagem_id: int, depois_de: int = 0) -> list:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT mensagens.*, usuarios.nome AS autor_nome, usuarios.perfil AS autor_perfil
                FROM mensagens
                JOIN usuarios ON usuarios.id = mensagens.autor_id
                WHERE mensagens.tatuagem_id = %s AND mensagens.id > %s
                ORDER BY mensagens.id
                """,
                (tatuagem_id, depois_de),
            )
            return [dict(item) for item in cursor.fetchall()]
