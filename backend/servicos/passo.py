from typing import Optional, Tuple

from repositorios import passo as repositorio_passo
from repositorios import tatuagem as repositorio_tatuagem
from servicos.tatuagem import pode_ver


# Lista o histórico somente se a tatuagem existir e a pessoa puder vê-la, para a rota responder 404.
# A regra usa quem está logado (o token), e não um cliente_id que a tela poderia trocar.
def listar_passos(tatuagem_id: int, usuario: dict) -> Optional[list]:
    if not pode_ver(repositorio_tatuagem.buscar_por_id(tatuagem_id), usuario):
        return None

    return repositorio_passo.listar_por_tatuagem(tatuagem_id)


# Apaga o histórico de um pedido existente e mantém o pedido ativo.
def limpar_historico(tatuagem_id: int) -> Optional[int]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None

    return repositorio_passo.descartar_por_tatuagem(tatuagem_id)


# Confere a regra e devolve uma tupla com passo, tatuagem e motivo para a rota escolher o status.
def registrar_passo(
    tatuagem_id: int, dados: dict
) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None, None, None

    tipo = dados["tipo"]
    # Cada tipo de passo leva a tatuagem para uma etapa.
    # A finalização encerra as sessões; o retoque vem depois, quando a pele já cicatrizou.
    etapas_por_tipo = {
        "pedido recebido": "pedida",
        "desenho aprovado": "desenho aprovado",
        "sessão": "em sessões",
        "finalização": "finalizada",
        "retoque": "retoque feito",
    }

    # Aceita somente as cinco etapas que o tatuador pode selecionar.
    if tipo not in etapas_por_tipo:
        return None, tatuagem, "Escolha uma etapa válida para este pedido."

    # Impede saltos que deixariam o histórico fora da sequência do fluxo.
    etapas_permitidas = {
        "pedido recebido": {"pedida"},
        "desenho aprovado": {"pedida", "desenho aprovado"},
        "sessão": {"desenho aprovado", "em sessões"},
        "finalização": {"em sessões", "finalizada"},
        "retoque": {"finalizada", "retoque feito"},
    }
    if tatuagem["etapa"] not in etapas_permitidas[tipo]:
        return None, tatuagem, "Esta etapa não pode ser registrada a partir da etapa atual."

    try:
        passo, tatuagem_atualizada = repositorio_passo.criar_e_atualizar_etapa(
            {
                "tatuagem_id": tatuagem_id,
                "tipo": tipo,
                "data": dados["data"],
                "observacao": dados.get("observacao", ""),
            },
            etapas_por_tipo[tipo],
        )
    except LookupError:
        return None, None, None
    passo_com_etapa = {**passo, "etapa_atualizada": tatuagem_atualizada["etapa"]}
    return passo_com_etapa, tatuagem_atualizada, None
