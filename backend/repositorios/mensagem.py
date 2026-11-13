from contextlib import closing
from typing import Optional

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
            # Guarda até qual mensagem cada pessoa já leu em cada conversa.
            # A chave primária composta (usuario_id, tatuagem_id) garante uma única linha por pessoa e pedido.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS leituras_mensagens (
                    usuario_id INTEGER NOT NULL,
                    tatuagem_id INTEGER NOT NULL,
                    ultima_lida_id INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (usuario_id, tatuagem_id),
                    CONSTRAINT fk_leituras_usuarios
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                    CONSTRAINT fk_leituras_tatuagens
                        FOREIGN KEY (tatuagem_id) REFERENCES tatuagens(id) ON DELETE CASCADE
                )
                """
            )
            # Foto anexada à mensagem (data URL), opcional. Acrescentada à tabela que já existe em produção.
            cursor.execute("ALTER TABLE mensagens ADD COLUMN IF NOT EXISTS imagem TEXT")
            banco.commit()


# Grava a mensagem e já devolve o nome e o perfil de quem escreveu, para a tela montar o balão.
# O WITH (CTE) guarda a linha recém-inserida com um nome, e o SELECT seguinte a junta com o usuário.
# imagem é opcional: a mensagem pode ter só texto, só foto ou os dois.
def criar(tatuagem_id: int, autor_id: int, texto: str, imagem: Optional[str] = None) -> dict:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH nova AS (
                    INSERT INTO mensagens (tatuagem_id, autor_id, texto, imagem)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                )
                SELECT nova.*, usuarios.nome AS autor_nome, usuarios.perfil AS autor_perfil
                FROM nova
                JOIN usuarios ON usuarios.id = nova.autor_id
                """,
                (tatuagem_id, autor_id, texto, imagem),
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


# Marca a conversa como lida até a mensagem ate_id.
# ON CONFLICT atualiza a linha que já existe em vez de criar outra; GREATEST nunca deixa a marca voltar para trás.
def marcar_lidas(usuario_id: int, tatuagem_id: int, ate_id: int) -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO leituras_mensagens (usuario_id, tatuagem_id, ultima_lida_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (usuario_id, tatuagem_id)
                DO UPDATE SET ultima_lida_id = GREATEST(leituras_mensagens.ultima_lida_id, EXCLUDED.ultima_lida_id)
                """,
                (usuario_id, tatuagem_id, ate_id),
            )
            banco.commit()


# Conta, por pedido, as mensagens que a pessoa ainda não leu e traz a última delas para o aviso.
# Só conta o que veio do outro lado: a cliente é avisada do estúdio, e o tatuador, das clientes.
# LEFT JOIN mantém as conversas que a pessoa nunca abriu; COALESCE trata essa falta de leitura como zero.
# cliente_id, quando informado, limita a busca aos pedidos daquela cliente.
def listar_nao_lidas(usuario_id: int, perfil: str, cliente_id: Optional[int] = None) -> list:
    filtro_cliente = "AND tatuagens.cliente_id = %s" if cliente_id is not None else ""
    parametros = [usuario_id, perfil] + ([cliente_id] if cliente_id is not None else [])

    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                WITH pendentes AS (
                    SELECT mensagens.tatuagem_id, COUNT(*) AS nao_lidas, MAX(mensagens.id) AS ultima_id
                    FROM mensagens
                    JOIN tatuagens ON tatuagens.id = mensagens.tatuagem_id
                    JOIN usuarios AS autor ON autor.id = mensagens.autor_id
                    LEFT JOIN leituras_mensagens AS leitura
                        ON leitura.tatuagem_id = mensagens.tatuagem_id AND leitura.usuario_id = %s
                    WHERE autor.perfil <> %s
                      AND mensagens.id > COALESCE(leitura.ultima_lida_id, 0)
                      {filtro_cliente}
                    GROUP BY mensagens.tatuagem_id
                )
                SELECT pendentes.*, tatuagens.ideia,
                       -- Mensagem só com foto não tem texto; o aviso mostra "Enviou uma foto" no lugar.
                       CASE WHEN ultima.texto = '' THEN 'Enviou uma foto' ELSE ultima.texto END AS ultimo_texto,
                       autor.nome AS ultimo_autor
                FROM pendentes
                JOIN tatuagens ON tatuagens.id = pendentes.tatuagem_id
                JOIN mensagens AS ultima ON ultima.id = pendentes.ultima_id
                JOIN usuarios AS autor ON autor.id = ultima.autor_id
                ORDER BY pendentes.ultima_id DESC
                """,
                tuple(parametros),
            )
            return [dict(item) for item in cursor.fetchall()]
