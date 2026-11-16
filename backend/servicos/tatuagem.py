from typing import Optional

from repositorios import passo as repositorio_passo
from repositorios import tatuagem as repositorio_tatuagem
from servicos.usuario import GRUPO_TATUADOR


# Regra de acesso aos pedidos: o tatuador vê todos; a cliente, só os dela.
# Fica num lugar só para todas as rotas de pedido seguirem a mesma regra.
def pode_ver(tatuagem: Optional[dict], usuario: dict) -> bool:
    if tatuagem is None:
        return False
    return usuario["perfil"] == GRUPO_TATUADOR or tatuagem["cliente_id"] == usuario["id"]


# Aplica a etapa inicial definida na cartilha antes de guardar um novo pedido.
# A imagem da IA, quando vem, é guardada à parte, ligada ao pedido recém-criado.
# A cliente sempre pede para si mesma: o cliente_id vem do token, não do que a tela mandou.
def criar_tatuagem(dados: dict, usuario: dict) -> dict:
    if usuario["perfil"] != GRUPO_TATUADOR:
        dados = {**dados, "cliente_id": usuario["id"]}
    tatuagem = repositorio_tatuagem.criar(dados)
    if dados.get("imagem_ia"):
        repositorio_tatuagem.salvar_imagem(tatuagem["id"], dados["imagem_ia"])
    repositorio_tatuagem.salvar_propostas_ia(tatuagem["id"], dados.get("imagens_ia", []))
    return tatuagem


# Devolve a imagem da IA do pedido, ou None quando não existe ou a pessoa não pode ver.
# O tatuador vê a de qualquer pedido; a cliente, só a dos pedidos dela.
def buscar_imagem(tatuagem_id: int, usuario: dict) -> Optional[str]:
    if not pode_ver(repositorio_tatuagem.buscar_por_id(tatuagem_id), usuario):
        return None
    return repositorio_tatuagem.buscar_imagem(tatuagem_id)


def listar_propostas_ia(tatuagem_id: int, usuario: dict) -> Optional[list[str]]:
    if not pode_ver(repositorio_tatuagem.buscar_por_id(tatuagem_id), usuario):
        return None
    return repositorio_tatuagem.listar_propostas_ia(tatuagem_id)


# Busca uma tatuagem para a rota responder com os dados ou com status 404.
# Pedido de outra cliente também vira 404, para não revelar que aquele número existe.
def buscar_tatuagem(tatuagem_id: int, usuario: dict) -> Optional[dict]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    return tatuagem if pode_ver(tatuagem, usuario) else None


# Entrega à rota a lista filtrada pela etapa e pelo cliente, quando informados.
# Para a cliente, o filtro é sempre ela mesma, seja qual for o cliente_id pedido.
def listar_tatuagens(usuario: dict, etapa: Optional[str] = None, cliente_id: Optional[int] = None) -> list:
    if usuario["perfil"] != GRUPO_TATUADOR:
        cliente_id = usuario["id"]
    return repositorio_tatuagem.listar(etapa, cliente_id)


# Descarta o pedido e remove também os passos ligados a ele.
def descartar_tatuagem(tatuagem_id: int) -> Optional[dict]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None

    repositorio_passo.descartar_por_tatuagem(tatuagem_id)
    return repositorio_tatuagem.descartar(tatuagem_id)
