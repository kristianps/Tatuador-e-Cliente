import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from servicos import passo as servico_passo
from servicos import tatuagem as servico_tatuagem
from servicos import usuario as servico_usuario

BRUNA = {"id": 3, "nome": "Bruna", "email": "bruna@x.com", "perfil": "cliente"}
VITOR = {"id": 1, "nome": "Vitor", "email": "vitor@x.com", "perfil": "tatuador"}
PEDIDO_DA_BRUNA = {"id": 7, "cliente_id": 3, "ideia": "Lua", "local_corpo": "Braço", "tamanho_cm": 8, "etapa": "pedida"}
PEDIDO_DE_OUTRA = {**PEDIDO_DA_BRUNA, "id": 8, "cliente_id": 99}
PEDIDOS = {7: PEDIDO_DA_BRUNA, 8: PEDIDO_DE_OUTRA}


class PermissoesTests(unittest.TestCase):
    """Chama as rotas de verdade, trocando só o banco por dados de mentira."""

    def setUp(self):
        self.cliente = TestClient(main.app)
        repositorio = servico_tatuagem.repositorio_tatuagem
        simulacoes = [
            patch.object(repositorio, "buscar_por_id", side_effect=PEDIDOS.get),
            patch.object(repositorio, "listar", side_effect=self._listar),
            patch.object(repositorio, "criar", side_effect=lambda dados: {**PEDIDO_DA_BRUNA, "cliente_id": dados["cliente_id"]}),
            patch.object(repositorio, "salvar_propostas_ia"),
            patch.object(repositorio, "descartar", side_effect=PEDIDOS.get),
            patch.object(servico_tatuagem.repositorio_passo, "descartar_por_tatuagem", return_value=0),
            patch.object(servico_passo.repositorio_passo, "listar_por_tatuagem", return_value=[]),
        ]
        for simulacao in simulacoes:
            simulacao.start()
            self.addCleanup(simulacao.stop)

    @staticmethod
    def _listar(etapa=None, cliente_id=None):
        return [p for p in PEDIDOS.values() if cliente_id is None or p["cliente_id"] == cliente_id]

    def _como(self, usuario):
        main.app.dependency_overrides[servico_usuario.obter_usuario_atual] = lambda: usuario
        self.addCleanup(main.app.dependency_overrides.clear)

    def test_cliente_so_lista_os_proprios_pedidos_mesmo_pedindo_outro_cliente(self):
        self._como(BRUNA)
        for caminho in ("/tatuagens", "/tatuagens?cliente_id=99"):
            resposta = self.cliente.get(caminho)
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual([p["id"] for p in resposta.json()], [7])

    def test_tatuador_lista_todos(self):
        self._como(VITOR)
        self.assertEqual(len(self.cliente.get("/tatuagens").json()), 2)

    def test_cliente_nao_ve_pedido_nem_historico_de_outra(self):
        self._como(BRUNA)
        self.assertEqual(self.cliente.get("/tatuagens/8").status_code, 404)
        self.assertEqual(self.cliente.get("/tatuagens/8/passos").status_code, 404)
        self.assertEqual(self.cliente.get("/tatuagens/8/imagens-ia").status_code, 404)
        self.assertEqual(self.cliente.get("/tatuagens/7").status_code, 200)
        self.assertEqual(self.cliente.get("/tatuagens/7/passos").status_code, 200)

    def test_cliente_nao_faz_pedido_em_nome_de_outra(self):
        self._como(BRUNA)
        resposta = self.cliente.post(
            "/tatuagens", json={"cliente_id": 99, "ideia": "Lua", "local_corpo": "Braço", "tamanho_cm": 8}
        )
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["cliente_id"], 3)

    def test_tatuador_pode_fazer_pedido_para_uma_cliente(self):
        self._como(VITOR)
        resposta = self.cliente.post(
            "/tatuagens", json={"cliente_id": 99, "ideia": "Lua", "local_corpo": "Braço", "tamanho_cm": 8}
        )
        self.assertEqual(resposta.json()["cliente_id"], 99)

    def test_cliente_nao_apaga_pedido_nem_mexe_nas_etapas(self):
        self._como(BRUNA)
        self.assertEqual(self.cliente.delete("/tatuagens/7").status_code, 403)
        self.assertEqual(self.cliente.delete("/tatuagens/7/passos").status_code, 403)
        resposta = self.cliente.post("/tatuagens/7/passos", json={"tipo": "desenho aprovado", "data": "2026-01-10"})
        self.assertEqual(resposta.status_code, 403)

    def test_tatuador_apaga_pedido(self):
        self._como(VITOR)
        self.assertEqual(self.cliente.delete("/tatuagens/7").status_code, 204)


if __name__ == "__main__":
    unittest.main()
