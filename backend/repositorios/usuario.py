from contextlib import closing
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

import configuracao
import seguranca


def _conectar():
    if not configuracao.URL_DO_BANCO:
        raise RuntimeError("URL_DO_BANCO não foi configurada. Defina a variável de ambiente no projeto da Vercel.")
    return psycopg2.connect(configuracao.URL_DO_BANCO)


# Cria a tabela de usuários e mantém cada e-mail único para evitar contas duplicadas.
def inicializar() -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(120) NOT NULL,
                    email VARCHAR(180) NOT NULL UNIQUE,
                    senha_hash VARCHAR(255) NOT NULL,
                    perfil VARCHAR(30) NOT NULL
                )
                """
            )
            # Guarda os pedidos de recuperação de senha. ON DELETE CASCADE apaga os pedidos junto com a conta.
            # TIMESTAMPTZ é uma data com fuso horário, para a validade não depender do fuso do servidor.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recuperacoes_senha (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    token_hash CHAR(64) NOT NULL UNIQUE,
                    expira_em TIMESTAMPTZ NOT NULL,
                    usado_em TIMESTAMPTZ,
                    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            # Sem isso, a tabela ficaria aberta pela API pública do Supabase; as outras tabelas também usam RLS.
            cursor.execute("ALTER TABLE recuperacoes_senha ENABLE ROW LEVEL SECURITY")
            # Guarda as tentativas de login erradas, para bloquear quem tenta adivinhar senhas.
            # Usa o e-mail digitado, e não o id, para contar também e-mails que não têm conta.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS falhas_login (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(180) NOT NULL,
                    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS falhas_login_email ON falhas_login (email, criado_em)")
            cursor.execute("ALTER TABLE falhas_login ENABLE ROW LEVEL SECURITY")
            # Campos do cadastro presencial, acrescentados à tabela que já existe em produção.
            # origem diz como a conta nasceu: 'site' (a própria pessoa se cadastrou) ou 'presencial' (o estúdio cadastrou).
            # DEFAULT 'site' preenche as contas antigas, que todas vieram do site.
            cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS telefone VARCHAR(30)")
            cursor.execute(
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS origem VARCHAR(20) NOT NULL DEFAULT 'site'"
            )
            banco.commit()


# Cria os perfis padrão do sistema, com cliente e tatuador, para a aula de login funcionar no demo.
def criar_usuarios_iniciais() -> None:
    usuarios = [
        ("Vitor", "vitor@pereiratatto.com", "vitor123", "tatuador"),
        ("Bruna", "bruna@pereiratatto.com", "bruna123", "cliente"),
    ]

    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            for nome, email, senha, perfil in usuarios:
                cursor.execute(
                    "SELECT senha_hash FROM usuarios WHERE email = %s",
                    (email.lower(),),
                )
                usuario_existente = cursor.fetchone()

                # Mantém o hash salvo quando ele já confere e está no formato atual;
                # assim o banco não é reescrito a cada vez que a API inicia.
                if usuario_existente is not None and seguranca.verificar_senha(
                    senha, usuario_existente[0]
                ) and not seguranca.precisa_atualizar(usuario_existente[0]):
                    senha_hash = usuario_existente[0]
                else:
                    senha_hash = seguranca.gerar_hash_senha(senha)

                if usuario_existente is None:
                    cursor.execute(
                        """
                        INSERT INTO usuarios (nome, email, senha_hash, perfil)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (nome, email.lower(), senha_hash, perfil),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE usuarios
                        SET nome = %s,
                            senha_hash = %s,
                            perfil = %s
                        WHERE email = %s
                        """,
                        (nome, senha_hash, perfil, email.lower()),
                    )
            banco.commit()


# Busca usando o e-mail para validar o login.
def buscar_por_email(email: str):
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email.lower(),))
            usuario = cursor.fetchone()
            return dict(usuario) if usuario is not None else None


# Busca pelo identificador para montar a sessão autenticada.
def buscar_por_id(usuario_id: int):
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()
            return dict(usuario) if usuario is not None else None


# Cria uma nova conta para o sistema e retorna o usuário salvo.
# telefone e origem têm valor padrão, então o cadastro pelo site continua chamando igual.
def criar_usuario(
    nome: str,
    email: str,
    senha: str,
    perfil: str = "cliente",
    telefone: Optional[str] = None,
    origem: str = "site",
):
    email_normalizado = email.lower().strip()
    senha_hash = seguranca.gerar_hash_senha(senha)

    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = %s",
                (email_normalizado,),
            )
            if cursor.fetchone() is not None:
                raise ValueError("Já existe uma conta cadastrada com este e-mail.")

            cursor.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash, perfil, telefone, origem)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, nome, email, perfil, telefone, origem
                """,
                (nome.strip(), email_normalizado, senha_hash, perfil.lower(), telefone, origem),
            )
            usuario = cursor.fetchone()
            banco.commit()
            return dict(usuario)


# Lista as clientes para o estúdio, com quantos pedidos cada uma já fez.
# A subconsulta entre parênteses conta os pedidos de cada linha; nunca devolve a senha.
def listar_clientes() -> list:
    with closing(_conectar()) as banco:
        with banco.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT usuarios.id, usuarios.nome, usuarios.email, usuarios.telefone, usuarios.origem,
                       (SELECT COUNT(*) FROM tatuagens WHERE tatuagens.cliente_id = usuarios.id) AS pedidos
                FROM usuarios
                WHERE usuarios.perfil = 'cliente'
                ORDER BY usuarios.id DESC
                """
            )
            return [dict(item) for item in cursor.fetchall()]


# Conta os pedidos da última hora para limitar quantos e-mails uma conta pode receber.
def contar_recuperacoes_recentes(usuario_id: int) -> int:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM recuperacoes_senha
                WHERE usuario_id = %s AND criado_em > NOW() - INTERVAL '1 hour'
                """,
                (usuario_id,),
            )
            return cursor.fetchone()[0]


# Registra um novo pedido e cancela os anteriores, para só o link mais recente funcionar.
def criar_recuperacao(usuario_id: int, token_hash: str, minutos_validade: int) -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recuperacoes_senha SET usado_em = NOW()
                WHERE usuario_id = %s AND usado_em IS NULL
                """,
                (usuario_id,),
            )
            # A validade é calculada pelo relógio do banco, o mesmo usado na hora de conferir o link.
            cursor.execute(
                """
                INSERT INTO recuperacoes_senha (usuario_id, token_hash, expira_em)
                VALUES (%s, %s, NOW() + make_interval(mins => %s))
                """,
                (usuario_id, token_hash, minutos_validade),
            )
            banco.commit()


# Troca a senha se o link for válido. Tudo ocorre em uma transação: ou o link é gasto e a senha muda, ou nada muda.
def redefinir_senha_por_token(token_hash: str, senha_hash: str) -> bool:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            # O UPDATE confere e gasta o link de uma vez, então dois envios simultâneos não usam o mesmo link.
            cursor.execute(
                """
                UPDATE recuperacoes_senha SET usado_em = NOW()
                WHERE token_hash = %s AND usado_em IS NULL AND expira_em > NOW()
                RETURNING usuario_id
                """,
                (token_hash,),
            )
            recuperacao = cursor.fetchone()
            if recuperacao is None:
                return False

            cursor.execute(
                "UPDATE usuarios SET senha_hash = %s WHERE id = %s",
                (senha_hash, recuperacao[0]),
            )
            banco.commit()
            return True


# Grava um novo hash para a conta; usado para migrar senhas antigas para o formato com sal próprio.
def atualizar_senha_hash(usuario_id: int, senha_hash: str) -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                "UPDATE usuarios SET senha_hash = %s WHERE id = %s",
                (senha_hash, usuario_id),
            )
            banco.commit()


# Conta as tentativas erradas recentes deste e-mail.
def contar_falhas_login(email: str, minutos: int) -> int:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM falhas_login
                WHERE email = %s AND criado_em > NOW() - make_interval(mins => %s)
                """,
                (email.lower().strip(), minutos),
            )
            return cursor.fetchone()[0]


# Anota uma tentativa errada e aproveita para apagar as de mais de um dia, que já não contam.
def registrar_falha_login(email: str) -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute("DELETE FROM falhas_login WHERE criado_em < NOW() - INTERVAL '1 day'")
            cursor.execute("INSERT INTO falhas_login (email) VALUES (%s)", (email.lower().strip(),))
            banco.commit()


# Depois de um login certo, as tentativas erradas anteriores deixam de contar.
def limpar_falhas_login(email: str) -> None:
    with closing(_conectar()) as banco:
        with banco.cursor() as cursor:
            cursor.execute("DELETE FROM falhas_login WHERE email = %s", (email.lower().strip(),))
            banco.commit()
