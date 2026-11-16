import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import configuracao
import seguranca
from servicos import usuario as servico


def _hash_formato_antigo(senha: str, segredo: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), segredo.encode("utf-8"), 100_000).hex()


def _credencial(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


USUARIO = {
    "id": 3,
    "nome": "Bruna",
    "email": "bruna@pereiratatto.com",
    "perfil": "cliente",
}


class HashDeSenhaTests(unittest.TestCase):
    def test_confere_a_senha_certa_e_recusa_a_errada(self):
        senha_hash = seguranca.gerar_hash_senha("bruna123")
        self.assertTrue(seguranca.verificar_senha("bruna123", senha_hash))
        self.assertFalse(seguranca.verificar_senha("bruna124", senha_hash))

    def test_mesma_senha_gera_hashes_diferentes(self):
        self.assertNotEqual(seguranca.gerar_hash_senha("igual"), seguranca.gerar_hash_senha("igual"))

    def test_aceita_hash_antigo_feito_com_a_chave_padrao(self):
        antigo = _hash_formato_antigo("vitor123", "pereiratatto-secreto-demo")
        self.assertTrue(seguranca.verificar_senha("vitor123", antigo))
        self.assertFalse(seguranca.verificar_senha("errada", antigo))
        self.assertTrue(seguranca.precisa_atualizar(antigo))

    def test_hash_atual_nao_precisa_atualizar(self):
        self.assertFalse(seguranca.precisa_atualizar(seguranca.gerar_hash_senha("x")))

    def test_hash_corrompido_nao_quebra(self):
        self.assertFalse(seguranca.verificar_senha("x", "pbkdf2_sha256$abc$zz$yy"))
        self.assertFalse(seguranca.verificar_senha("x", ""))


class LoginTests(unittest.TestCase):
    def test_senha_errada_nao_autentica(self):
        usuario = {**USUARIO, "senha_hash": seguranca.gerar_hash_senha("bruna123")}
        with patch.object(servico.repositorio_usuario, "buscar_por_email", return_value=usuario):
            self.assertIsNone(servico.autenticar_usuario(USUARIO["email"], "errada"))

    def test_email_inexistente_nao_autentica(self):
        with patch.object(servico.repositorio_usuario, "buscar_por_email", return_value=None):
            self.assertIsNone(servico.autenticar_usuario("ninguem@x.com", "qualquer"))

    def test_login_com_hash_antigo_migra_para_o_formato_novo(self):
        usuario = {**USUARIO, "senha_hash": _hash_formato_antigo("bruna123", "pereiratatto-secreto-demo")}
        with (
            patch.object(servico.repositorio_usuario, "buscar_por_email", return_value=usuario),
            patch.object(servico.repositorio_usuario, "atualizar_senha_hash") as atualizar,
        ):
            self.assertIsNotNone(servico.autenticar_usuario(USUARIO["email"], "bruna123"))

        usuario_id, novo_hash = atualizar.call_args.args
        self.assertEqual(usuario_id, 3)
        self.assertFalse(seguranca.precisa_atualizar(novo_hash))
        self.assertTrue(seguranca.verificar_senha("bruna123", novo_hash))

    def test_login_com_hash_atual_nao_regrava(self):
        usuario = {**USUARIO, "senha_hash": seguranca.gerar_hash_senha("bruna123")}
        with (
            patch.object(servico.repositorio_usuario, "buscar_por_email", return_value=usuario),
            patch.object(servico.repositorio_usuario, "atualizar_senha_hash") as atualizar,
        ):
            servico.autenticar_usuario(USUARIO["email"], "bruna123")
        atualizar.assert_not_called()


class TokenTests(unittest.TestCase):
    def test_token_tem_data_de_validade(self):
        payload = jwt.decode(
            servico.gerar_token(USUARIO), configuracao.JWT_SECRET_KEY, algorithms=[configuracao.JWT_ALGORITHM]
        )
        validade = datetime.fromtimestamp(payload["exp"], timezone.utc)
        esperado = datetime.now(timezone.utc) + timedelta(hours=configuracao.JWT_HORAS_VALIDADE)
        self.assertLess(abs((validade - esperado).total_seconds()), 60)

    def test_token_valido_devolve_o_usuario(self):
        with patch.object(servico.repositorio_usuario, "buscar_por_id", return_value=USUARIO) as buscar:
            usuario = servico.obter_usuario_atual(_credencial(servico.gerar_token(USUARIO)))
        self.assertEqual(usuario["id"], 3)
        buscar.assert_called_once_with(3)

    def test_token_vencido_e_recusado(self):
        vencido = jwt.encode(
            {"sub": "3", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            configuracao.JWT_SECRET_KEY,
            algorithm=configuracao.JWT_ALGORITHM,
        )
        with self.assertRaises(HTTPException) as erro:
            servico.obter_usuario_atual(_credencial(vencido))
        self.assertEqual(erro.exception.status_code, 401)

    def test_token_assinado_com_outra_chave_e_recusado(self):
        falso = jwt.encode(
            {"sub": "3", "perfil": "tatuador", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "uma-chave-qualquer-que-nao-e-a-do-servidor-123",
            algorithm="HS256",
        )
        with self.assertRaises(HTTPException) as erro:
            servico.obter_usuario_atual(_credencial(falso))
        self.assertEqual(erro.exception.status_code, 401)

    def test_usuario_apagado_e_recusado(self):
        with patch.object(servico.repositorio_usuario, "buscar_por_id", return_value=None):
            with self.assertRaises(HTTPException) as erro:
                servico.obter_usuario_atual(_credencial(servico.gerar_token(USUARIO)))
        self.assertEqual(erro.exception.status_code, 401)


class SemChaveJwtTests(unittest.TestCase):
    def setUp(self):
        sem_chave = patch.multiple(configuracao, JWT_SECRET_KEY="", JWT_CONFIGURADA=False)
        sem_chave.start()
        self.addCleanup(sem_chave.stop)

    def test_login_responde_503_sem_consultar_o_banco(self):
        with patch.object(servico.repositorio_usuario, "buscar_por_email") as buscar:
            with self.assertRaises(HTTPException) as erro:
                servico.autenticar_usuario(USUARIO["email"], "bruna123")
        self.assertEqual(erro.exception.status_code, 503)
        buscar.assert_not_called()

    def test_rota_protegida_responde_503(self):
        with self.assertRaises(HTTPException) as erro:
            servico.obter_usuario_atual(_credencial("qualquer.token.aqui"))
        self.assertEqual(erro.exception.status_code, 503)

    def test_api_inicia_e_health_avisa_sem_a_chave(self):
        # Processo separado, sem .env e sem banco, como um deploy na Vercel sem a variável.
        import os
        import subprocess
        import sys

        codigo = (
            "import dotenv; dotenv.load_dotenv = lambda *a, **k: False\n"
            "import main\n"
            "print(main.health_check()['jwt'])\n"
        )
        ambiente = {chave: valor for chave, valor in os.environ.items() if chave not in ("JWT_SECRET_KEY", "URL_DO_BANCO")}
        pasta_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resultado = subprocess.run(
            [sys.executable, "-c", codigo], cwd=pasta_backend, env=ambiente,
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("not-configured", resultado.stdout)


class PerfilTests(unittest.TestCase):
    def test_cliente_nao_acessa_rota_de_tatuador(self):
        guarda = servico.requerer_perfil({servico.GRUPO_TATUADOR})
        with self.assertRaises(HTTPException) as erro:
            guarda(usuario=USUARIO)
        self.assertEqual(erro.exception.status_code, 403)

    def test_tatuador_acessa_rota_de_tatuador(self):
        tatuador = {**USUARIO, "perfil": "tatuador"}
        guarda = servico.requerer_perfil({servico.GRUPO_TATUADOR})
        self.assertIs(guarda(usuario=tatuador), tatuador)


class RecuperacaoSenhaTests(unittest.TestCase):
    def setUp(self):
        config = patch.multiple(
            servico,
            SMTP_USUARIO="estudio@x.com",
            SMTP_SENHA="senha",
            EMAIL_REMETENTE="estudio@x.com",
            URL_DO_SITE="https://site",
        )
        config.start()
        self.addCleanup(config.stop)
        buscar = patch.object(servico.repositorio_usuario, "buscar_por_email", return_value=USUARIO)
        buscar.start()
        self.addCleanup(buscar.stop)

    def test_bloqueia_depois_do_limite_por_hora(self):
        with (
            patch.object(
                servico.repositorio_usuario,
                "contar_recuperacoes_recentes",
                return_value=servico.MAXIMO_RECUPERACOES_POR_HORA,
            ),
            patch.object(servico.repositorio_usuario, "criar_recuperacao") as criar,
            patch.object(servico, "_enviar_email_recuperacao") as enviar,
        ):
            servico.solicitar_recuperacao_senha(USUARIO["email"])
        criar.assert_not_called()
        enviar.assert_not_called()

    def test_abaixo_do_limite_salva_so_o_hash_do_codigo(self):
        with (
            patch.object(servico.repositorio_usuario, "contar_recuperacoes_recentes", return_value=0),
            patch.object(servico.repositorio_usuario, "criar_recuperacao") as criar,
            patch.object(servico, "_enviar_email_recuperacao") as enviar,
        ):
            servico.solicitar_recuperacao_senha(USUARIO["email"])

        token_enviado = enviar.call_args.args[1]
        token_salvo = criar.call_args.args[1]
        self.assertNotEqual(token_enviado, token_salvo)
        self.assertEqual(token_salvo, hashlib.sha256(token_enviado.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    unittest.main()
