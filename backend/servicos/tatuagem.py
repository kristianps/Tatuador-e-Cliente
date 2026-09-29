from typing import Optional

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
