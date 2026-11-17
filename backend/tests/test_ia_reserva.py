import unittest
from unittest.mock import patch

from servicos import ia

USUARIO = {"id": 5, "perfil": "cliente"}


def _fala(texto, imagem=None):
    return {"papel": "cliente", "texto": texto, "imagem": imagem}


class TrocaDeModeloTests(unittest.TestCase):
    def test_passa_para_o_proximo_modelo_quando_um_falha(self):
        tentados = []

        def responder(modelo, *args):
            tentados.append(modelo)
            return "Oi!" if modelo == "modelo-c" else None  # a e b com cota esgotada

        with (
            patch.object(ia.configuracao, "GOOGLE_API_KEY", "chave"),
            patch.object(ia.configuracao, "GOOGLE_MODELOS_TEXTO", ["modelo-a", "modelo-b", "modelo-c", "modelo-d"]),
            patch.object(ia, "_texto_google_modelo", side_effect=responder),
            patch.object(ia, "_texto_openrouter") as reserva,
        ):
            self.assertEqual(ia._gerar_texto("instrução", [_fala("oi")]), "Oi!")
        self.assertEqual(tentados, ["modelo-a", "modelo-b", "modelo-c"])
        reserva.assert_not_called()

    def test_usa_a_openrouter_quando_todo_o_google_falha(self):
        with (
            patch.object(ia.configuracao, "GOOGLE_API_KEY", "chave"),
            patch.object(ia.configuracao, "GOOGLE_MODELOS_TEXTO", ["modelo-a", "modelo-b"]),
            patch.object(ia, "_texto_google_modelo", return_value=None),
            patch.object(ia, "_texto_openrouter", return_value="Olá pela reserva") as reserva,
        ):
            self.assertEqual(ia._gerar_texto("instrução", [_fala("oi")]), "Olá pela reserva")
        reserva.assert_called_once()

    def test_para_de_tentar_quando_o_tempo_acaba(self):
        with (
            patch.object(ia.configuracao, "GOOGLE_API_KEY", "chave"),
            patch.object(ia.configuracao, "GOOGLE_MODELOS_TEXTO", ["modelo-a", "modelo-b"]),
            patch.object(ia, "TEMPO_TOTAL", 1),  # menos que o mínimo de 2 s para uma tentativa
            patch.object(ia, "_texto_google_modelo") as google,
        ):
            self.assertIsNone(ia._gerar_texto("instrução", [_fala("oi")]))
        google.assert_not_called()

    def test_so_pede_raciocinio_curto_para_modelos_que_aceitam(self):
        with patch.object(ia, "_post_json", return_value=None) as post:
            ia._texto_google_modelo("gemini-3.1-flash-lite", "x", [_fala("oi")], False, 5)
            ia._texto_google_modelo("gemma-4-31b-it", "x", [_fala("oi")], False, 5)
        com, sem = (chamada.args[2]["generationConfig"] for chamada in post.call_args_list)
        self.assertIn("thinkingConfig", com)
        self.assertNotIn("thinkingConfig", sem)


class ConversaSemErroTests(unittest.TestCase):
    def setUp(self):
        registrar = patch.object(ia.repositorio_ia, "registrar_uso")
        self.registrar = registrar.start()
        self.addCleanup(registrar.stop)

    def _conversar(self, historico, ia_responde=None, limite=None):
        with (
            patch.object(ia, "_motivo_limite", return_value=limite),
            patch.object(ia, "_gerar_texto", return_value=ia_responde),
        ):
            return ia.conversar(USUARIO, historico)

    def test_sem_ia_a_conversa_continua_com_pergunta_guia(self):
        resposta, motivo = self._conversar([_fala("Quero uma lua")])
        self.assertIsNone(motivo)
        self.assertIn("estilo", resposta)
        self.registrar.assert_not_called()  # a resposta-guia não gasta a cota

    def test_limite_diario_tambem_vira_pergunta_guia(self):
        resposta, motivo = self._conversar([_fala("Quero uma lua")], limite="limite")
        self.assertIsNone(motivo)
        self.assertTrue(resposta)

    def test_pergunta_guia_segue_o_que_ainda_falta(self):
        guia = ia._resposta_guia
        self.assertIn("parte do corpo", guia([_fala("Quero uma lua em fineline")]))
        self.assertIn("tamanho", guia([_fala("Lua fineline no antebraço")]))
        self.assertIn("significado", guia([_fala("Lua fineline no antebraço, 8 cm")]))
        final = guia([_fala("Lua fineline no antebraço, 8 cm, homenagem à minha avó")])
        self.assertIn("Usar esta conversa no meu pedido", final)

    def test_pergunta_guia_comenta_a_foto(self):
        resposta = ia._resposta_guia([_fala("", imagem="data:image/png;base64,AA")])
        self.assertIn("foto", resposta)


class SugestoesSemErroTests(unittest.TestCase):
    def test_sem_ia_devolve_sugestoes_prontas(self):
        tatuagem = {"id": 7, "cliente_id": 5, "ideia": "Lua", "local_corpo": "Braço", "tamanho_cm": 8, "etapa": "pedida"}
        with (
            patch.object(ia.repositorio_tatuagem, "buscar_por_id", return_value=tatuagem),
            patch.object(ia, "_motivo_limite", return_value=None),
            patch.object(ia.repositorio_mensagem, "listar_por_tatuagem", return_value=[]),
            patch.object(ia, "_gerar_texto", return_value=None),
        ):
            sugestoes, encontrada, motivo = ia.sugerir_respostas(USUARIO, 7)
            sugestoes_tatuador, _, _ = ia.sugerir_respostas({"id": 1, "perfil": "tatuador"}, 7)
        self.assertTrue(encontrada)
        self.assertIsNone(motivo)
        self.assertEqual(len(sugestoes), 3)
        self.assertIn("Recebi seu pedido", sugestoes_tatuador[0])


if __name__ == "__main__":
    unittest.main()
