from contextlib import closing

import psycopg2

import configuracao


def _conectar():
    if not configuracao.URL_DO_BANCO:
        raise RuntimeError("URL_DO_BANCO não foi configurada. Defina a variável de ambiente no projeto da Vercel.")
    return psycopg2.connect(configuracao.URL_DO_BANCO)


# Registra cada uso da IA (conversa, imagem ou sugestão), para limitar quanto cada pessoa usa por dia.
# Cada chamada à IA tem custo; sem limite, uma pessoa poderia gastar a cota do estúdio inteiro.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS uso_ia (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    tipo VARCHAR(20) NOT NULL,
                    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            # Sem isso, a tabela ficaria aberta pela API pública do Supabase, como as outras com RLS.
            cursor.execute("ALTER TABLE uso_ia ENABLE ROW LEVEL SECURITY")
            banco.commit()


# Conta quantas vezes a pessoa usou um tipo de recurso de IA nas últimas 24 horas.
def contar_uso_recente(usuario_id: int, tipo: str) -> int:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM uso_ia
                WHERE usuario_id = %s AND tipo = %s AND criado_em > NOW() - INTERVAL '24 hours'
                """,
                (usuario_id, tipo),
            )
            return cursor.fetchone()[0]


# Anota um uso que deu certo.
def registrar_uso(usuario_id: int, tipo: str) -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute("INSERT INTO uso_ia (usuario_id, tipo) VALUES (%s, %s)", (usuario_id, tipo))
            banco.commit()
