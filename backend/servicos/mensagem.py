from typing import Optional, Tuple

from repositorios import mensagem as repositorio_mensagem
from repositorios import tatuagem as repositorio_tatuagem
from servicos.usuario import GRUPO_TATUADOR


# Decide quem participa da conversa de um pedido: o tatuador vê todas,
# e a cliente só a dos pedidos que são dela. Quem é o usuário vem do token, não da requisição.
def _pode_participar(tatuagem: dict, usuario: dict) -> bool:
    if usuario["perfil"] == GRUPO_TATUADOR:
        return True
    return tatuagem["cliente_id"] == usuario["id"]


# Devolve as mensagens do pedido, ou None quando ele não existe ou não pertence à cliente.
# Os dois casos viram 404 na rota, para não revelar que existe um pedido de outra pessoa.
def listar_mensagens(tatuagem_id: int, usuario: dict, depois_de: int = 0) -> Optional[list]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None or not _pode_participar(tatuagem, usuario):
        return None

    return repositorio_mensagem.listar_por_tatuagem(tatuagem_id, depois_de)


# Confere o acesso e o texto antes de gravar. Devolve uma tupla (mensagem, tatuagem, motivo),
# como o serviço de passos, para a rota escolher o status só com if.
def enviar_mensagem(
    tatuagem_id: int, usuario: dict, texto: str
) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None or not _pode_participar(tatuagem, usuario):
        return None, None, None

    # strip tira espaços e quebras de linha das pontas; uma mensagem só de espaços é recusada.
    texto_limpo = texto.strip()
    if not texto_limpo:
        return None, tatuagem, "Escreva uma mensagem antes de enviar."

    mensagem = repositorio_mensagem.criar(tatuagem_id, usuario["id"], texto_limpo)
    return mensagem, tatuagem, None
