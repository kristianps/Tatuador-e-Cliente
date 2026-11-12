from typing import Optional

from repositorios import passo as repositorio_passo
from repositorios import tatuagem as repositorio_tatuagem


# Aplica a etapa inicial definida na cartilha antes de guardar um novo pedido.
# A imagem da IA, quando vem, é guardada à parte, ligada ao pedido recém-criado.
def criar_tatuagem(dados: dict) -> dict:
    tatuagem = repositorio_tatuagem.criar(dados)
    if dados.get("imagem_ia"):
        repositorio_tatuagem.salvar_imagem(tatuagem["id"], dados["imagem_ia"])
    return tatuagem


# Devolve a imagem da IA do pedido, ou None quando não existe ou a pessoa não pode ver.
# O tatuador vê a de qualquer pedido; a cliente, só a dos pedidos dela.
def buscar_imagem(tatuagem_id: int, usuario: dict) -> Optional[str]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None
    if usuario["perfil"] != "tatuador" and tatuagem["cliente_id"] != usuario["id"]:
        return None
    return repositorio_tatuagem.buscar_imagem(tatuagem_id)


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
