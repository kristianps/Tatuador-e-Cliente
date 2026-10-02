from typing import Optional

from repositorios import passo as repositorio_passo
from repositorios import tatuagem as repositorio_tatuagem


# Aplica a etapa inicial definida na cartilha antes de guardar um novo pedido.
def criar_tatuagem(dados: dict) -> dict:
    return repositorio_tatuagem.criar(dados)


# Busca uma tatuagem para a rota responder com os dados ou com status 404.
def buscar_tatuagem(tatuagem_id: int) -> Optional[dict]:
    return repositorio_tatuagem.buscar_por_id(tatuagem_id)


# Entrega à rota a lista filtrada pela etapa e pelo cliente, quando informados.
def listar_tatuagens(etapa: Optional[str] = None, cliente_id: Optional[int] = None) -> list:
    return repositorio_tatuagem.listar(etapa, cliente_id)


# Descarta o pedido e remove também os passos ligados a ele.
def descartar_tatuagem(tatuagem_id: int) -> Optional[dict]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None

    repositorio_passo.descartar_por_tatuagem(tatuagem_id)
    return repositorio_tatuagem.descartar(tatuagem_id)
