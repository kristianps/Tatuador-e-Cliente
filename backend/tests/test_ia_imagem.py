import unittest
from unittest.mock import patch

from esquemas.tatuagem import TatuagemEntrada
from servicos import ia


class GeracaoDeImagemTests(unittest.TestCase):
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
