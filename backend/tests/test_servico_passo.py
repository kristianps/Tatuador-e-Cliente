import unittest
from datetime import date
from unittest.mock import patch

from servicos import passo


class RegistrarPassoTests(unittest.TestCase):
    def setUp(self):
        self.tatuagem = {"id": 7, "cliente_id": 3, "etapa": "pedida"}
        self.buscar = patch.object(
            passo.repositorio_tatuagem, "buscar_por_id", return_value=self.tatuagem
        )
        self.buscar.start()
        self.addCleanup(self.buscar.stop)

    def test_bloqueia_sessao_antes_da_aprovacao_do_desenho(self):
        with patch.object(passo.repositorio_passo, "criar_e_atualizar_etapa") as gravar:
            registro, tatuagem, motivo = passo.registrar_passo(
                7, {"tipo": "sessão", "data": date(2026, 1, 10)}
            )

        self.assertIsNone(registro)
        self.assertEqual(tatuagem["etapa"], "pedida")
        self.assertIn("etapa atual", motivo)
        gravar.assert_not_called()

    def test_registra_etapa_permitida_com_operacao_atomica(self):
        passo_criado = {"id": 11, "tatuagem_id": 7, "tipo": "desenho aprovado"}
        tatuagem_atualizada = {"id": 7, "etapa": "desenho aprovado"}
        with patch.object(
            passo.repositorio_passo,
            "criar_e_atualizar_etapa",
            return_value=(passo_criado, tatuagem_atualizada),
        ) as gravar:
            registro, tatuagem, motivo = passo.registrar_passo(
                7, {"tipo": "desenho aprovado", "data": date(2026, 1, 10)}
            )

        self.assertIsNone(motivo)
        self.assertEqual(tatuagem["etapa"], "desenho aprovado")
        self.assertEqual(registro["etapa_atualizada"], "desenho aprovado")
        gravar.assert_called_once()

    def test_permite_retoque_apos_finalizacao(self):
        self.tatuagem["etapa"] = "finalizada"
        with patch.object(
            passo.repositorio_passo,
            "criar_e_atualizar_etapa",
            return_value=(
                {"id": 12, "tatuagem_id": 7, "tipo": "retoque"},
                {"id": 7, "etapa": "retoque feito"},
            ),
        ) as gravar:
            registro, _, motivo = passo.registrar_passo(
                7, {"tipo": "retoque", "data": date(2026, 1, 10)}
            )

        self.assertIsNone(motivo)
        self.assertEqual(registro["etapa_atualizada"], "retoque feito")
        gravar.assert_called_once()

    def test_retorna_not_found_se_tatuagem_sumiu_antes_da_gravacao(self):
        with patch.object(
            passo.repositorio_passo,
            "criar_e_atualizar_etapa",
            side_effect=LookupError,
        ):
            registro, tatuagem, motivo = passo.registrar_passo(
                7, {"tipo": "desenho aprovado", "data": date(2026, 1, 10)}
            )

        self.assertIsNone(registro)
        self.assertIsNone(tatuagem)
        self.assertIsNone(motivo)


if __name__ == "__main__":
    unittest.main()
