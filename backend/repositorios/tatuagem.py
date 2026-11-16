from contextlib import closing
from typing import Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

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
            # Acrescenta o tamanho em centímetros na tabela que já existe em produção.
            # IF NOT EXISTS deixa o comando rodar em toda inicialização sem dar erro;
            # a coluna aceita vazio porque os pedidos antigos foram feitos sem tamanho.
            cursor.execute("ALTER TABLE tatuagens ADD COLUMN IF NOT EXISTS tamanho_cm INTEGER")
            # Resumo da IA em JSONB: o PostgreSQL guarda o objeto inteiro e o devolve já como dicionário.
            cursor.execute("ALTER TABLE tatuagens ADD COLUMN IF NOT EXISTS resumo_ia JSONB")
            # A imagem criada com a IA fica numa tabela à parte: ela é grande, e a lista de pedidos,
            # consultada a cada poucos segundos, não precisa carregá-la junto.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS imagens_tatuagem (
                    tatuagem_id INTEGER PRIMARY KEY REFERENCES tatuagens(id) ON DELETE CASCADE,
                    imagem TEXT NOT NULL
                )
                """
            )
            cursor.execute("ALTER TABLE imagens_tatuagem ENABLE ROW LEVEL SECURITY")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS propostas_ia_tatuagem (
                    id SERIAL PRIMARY KEY,
                    tatuagem_id INTEGER NOT NULL REFERENCES tatuagens(id) ON DELETE CASCADE,
                    imagem TEXT NOT NULL,
                    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute("ALTER TABLE propostas_ia_tatuagem ENABLE ROW LEVEL SECURITY")
            banco.commit()


# Guarda a imagem da IA de um pedido, no formato data URL (o tipo da imagem e o conteúdo em base64).
def salvar_imagem(tatuagem_id: int, imagem: str) -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO imagens_tatuagem (tatuagem_id, imagem) VALUES (%s, %s)
                ON CONFLICT (tatuagem_id) DO UPDATE SET imagem = EXCLUDED.imagem
                """,
                (tatuagem_id, imagem),
            )
            banco.commit()


# Busca a imagem da IA de um pedido, ou None quando o pedido não tem imagem.
def buscar_imagem(tatuagem_id: int) -> Optional[str]:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute("SELECT imagem FROM imagens_tatuagem WHERE tatuagem_id = %s", (tatuagem_id,))
            linha = cursor.fetchone()
            return linha[0] if linha is not None else None


def salvar_propostas_ia(tatuagem_id: int, imagens: list[str]) -> None:
    if not imagens:
        return
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO propostas_ia_tatuagem (tatuagem_id, imagem) VALUES (%s, %s)",
                [(tatuagem_id, imagem) for imagem in imagens],
            )
            banco.commit()


def listar_propostas_ia(tatuagem_id: int) -> list[str]:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                "SELECT imagem FROM propostas_ia_tatuagem WHERE tatuagem_id = %s ORDER BY id",
                (tatuagem_id,),
            )
            imagens = [linha[0] for linha in cursor.fetchall()]
    imagem_selecionada = buscar_imagem(tatuagem_id)
    if imagem_selecionada and imagem_selecionada not in imagens:
        imagens.append(imagem_selecionada)
    return imagens


def criar(dados: dict) -> dict:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO tatuagens (cliente_id, ideia, local_corpo, tamanho_cm, etapa, resumo_ia)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    dados["cliente_id"],
                    dados["ideia"],
                    dados["local_corpo"],
                    dados["tamanho_cm"],
                    "pedida",
                    # Json converte o dicionário para o formato que o PostgreSQL espera; None vira NULL.
                    Json(dados["resumo_ia"]) if dados.get("resumo_ia") else None,
                ),
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
