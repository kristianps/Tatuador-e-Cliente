import unittest
from unittest.mock import patch

from esquemas.tatuagem import TatuagemEntrada
from servicos import ia


class GeracaoDeImagemTests(unittest.TestCase):
    def test_prompt_recebe_ideia_local_tamanho_e_ajustes(self):
        usuario = {"id": 5}
        historico = [{"papel": "cliente", "texto": "Uma lua com flores", "imagem": None}]
        with (
            patch.object(ia, "_motivo_limite", return_value=None),
            patch.object(ia, "_imagem_openrouter", return_value="data:image/png;base64,AA") as gerar,
            patch.object(ia.repositorio_ia, "registrar_uso") as registrar,
        ):
            imagem, motivo = ia.gerar_imagem(
                usuario,
                historico,
                {"ideia": "Lua e lavanda", "local_corpo": "Antebraço", "tamanho_cm": 8, "ajustes": "Traço fino"},
            )

        prompt = gerar.call_args.args[0]
        self.assertEqual(imagem, "data:image/png;base64,AA")
        self.assertIsNone(motivo)
        self.assertIn("Lua e lavanda", prompt)
        self.assertIn("Antebraço", prompt)
        self.assertIn("8 cm", prompt)
        self.assertIn("Traço fino", prompt)
        registrar.assert_called_once_with(5, "imagem")

    def test_pedido_aceita_ate_tres_propostas_de_imagem(self):
        imagem = "data:image/png;base64,AA"
        entrada = TatuagemEntrada(
            cliente_id=1,
            ideia="Flores",
            local_corpo="Braço",
            tamanho_cm=8,
            imagens_ia=[imagem, imagem, imagem],
        )
        self.assertEqual(len(entrada.imagens_ia), 3)
        with self.assertRaises(ValueError):
            TatuagemEntrada(
                cliente_id=1,
                ideia="Flores",
                local_corpo="Braço",
                tamanho_cm=8,
                imagens_ia=[imagem] * 4,
            )


if __name__ == "__main__":
    unittest.main()
