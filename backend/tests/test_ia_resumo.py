import json
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from esquemas.ia import ResumoPedido
from esquemas.tatuagem import TatuagemEntrada
from servicos import ia

USUARIO = {"id": 5}
HISTORICO = [
    {"papel": "cliente", "texto": "Quero uma lua com lavanda no antebraço, uns 8 cm", "imagem": None},
    {"papel": "assistente", "texto": "Que tal em fineline, só em preto?", "imagem": None},
    {"papel": "cliente", "texto": "Gostei! É uma homenagem à minha avó", "imagem": None},
]


class ResumoPedidoTests(unittest.TestCase):
    def setUp(self):
        limite = patch.object(ia, "_motivo_limite", return_value=None)
        limite.start()
        self.addCleanup(limite.stop)
        registrar = patch.object(ia.repositorio_ia, "registrar_uso")
        self.registrar = registrar.start()
        self.addCleanup(registrar.stop)

    def _resumir(self, resposta_da_ia):
        with patch.object(ia, "_gerar_texto", return_value=resposta_da_ia) as gerar:
            resumo, motivo = ia.resumir_pedido(USUARIO, HISTORICO)
        return resumo, motivo, gerar

    def test_monta_o_resumo_e_envia_a_conversa_inteira(self):
        resposta = json.dumps({
            "estilo": "fineline",
            "elementos": ["lua", "lavanda"],
            "significado": "Homenagem à avó",
            "cores": "preto e cinza",
            "local_corpo": "Antebraço",
            "tamanho_cm": 8,
            "pendencias": ["A lua fica cheia ou crescente?"],
        })
        resumo, motivo, gerar = self._resumir(resposta)

        self.assertIsNone(motivo)
        self.assertEqual(resumo["estilo"], "fineline")
        self.assertEqual(resumo["elementos"], ["lua", "lavanda"])
        self.assertEqual(resumo["tamanho_cm"], 8)
        ResumoPedido(**resumo)  # o resultado precisa passar na validação da rota
        self.registrar.assert_called_once_with(5, "resumo")

        conversa = gerar.call_args.args[1][0]["texto"]
        self.assertIn("Cliente: Quero uma lua", conversa)
        self.assertIn("Assistente: Que tal em fineline", conversa)
        self.assertTrue(gerar.call_args.kwargs["saida_json"])

    def test_aceita_json_dentro_de_bloco_de_codigo(self):
        resumo, motivo, _ = self._resumir('```json\n{"estilo": "old school", "elementos": ["âncora"]}\n```')
        self.assertIsNone(motivo)
        self.assertEqual(resumo["estilo"], "old school")

    def test_corrige_campos_fora_do_formato(self):
        resposta = json.dumps({
            "estilo": "x" * 500,
            "elementos": "lua",  # deveria ser lista
            "tamanho_cm": 900,
            "pendencias": ["a", "", "b", "c", "d", "e", "f"],
            "cores": None,
        })
        resumo, motivo, _ = self._resumir(resposta)
        self.assertIsNone(motivo)
        self.assertEqual(len(resumo["estilo"]), 120)
        self.assertEqual(resumo["elementos"], [])
        self.assertIsNone(resumo["tamanho_cm"])
        self.assertEqual(resumo["pendencias"], ["a", "b", "c", "d"])
        self.assertEqual(resumo["cores"], "")
        ResumoPedido(**resumo)

    def test_resposta_vazia_ou_invalida_nao_conta_no_limite(self):
        for resposta in (None, "não é json", "[1, 2]", '{"pendencias": ["só pergunta"]}'):
            resumo, motivo, _ = self._resumir(resposta)
            self.assertIsNone(resumo)
            self.assertIn("Não foi possível resumir", motivo)
        self.registrar.assert_not_called()

    def test_respeita_o_limite_diario(self):
        with (
            patch.object(ia, "_motivo_limite", return_value="Você atingiu o limite diário"),
            patch.object(ia, "_gerar_texto") as gerar,
        ):
            resumo, motivo = ia.resumir_pedido(USUARIO, HISTORICO)
        self.assertIsNone(resumo)
        self.assertIn("limite", motivo)
        gerar.assert_not_called()


class ResumoNoPedidoTests(unittest.TestCase):
    def _pedido(self, **resumo):
        return TatuagemEntrada(cliente_id=1, ideia="Lua", local_corpo="Antebraço", tamanho_cm=8, resumo_ia=resumo)

    def test_pedido_aceita_resumo_revisado(self):
        pedido = self._pedido(estilo="fineline", elementos=["lua", " "], pendencias=["Cor?"])
        self.assertEqual(pedido.model_dump()["resumo_ia"]["elementos"], ["lua"])

    def test_pedido_sem_resumo_continua_valido(self):
        pedido = TatuagemEntrada(cliente_id=1, ideia="Lua", local_corpo="Antebraço", tamanho_cm=8)
        self.assertIsNone(pedido.resumo_ia)

    def test_recusa_resumo_grande_demais(self):
        with self.assertRaises(ValidationError):
            self._pedido(elementos=["x"] * 9)
        with self.assertRaises(ValidationError):
            self._pedido(significado="x" * 301)


if __name__ == "__main__":
    unittest.main()
