from typing import Optional, Tuple

from repositorios import passo as repositorio_passo
from repositorios import tatuagem as repositorio_tatuagem


# Lista o histórico somente se a tatuagem existir, para a rota distinguir o 404.
def listar_passos(tatuagem_id: int, cliente_id: Optional[int] = None) -> Optional[list]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None

    # Restringe a consulta da cliente às tatuagens associadas ao perfil informado.
    if cliente_id is not None and tatuagem["cliente_id"] != cliente_id:
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
    etapas_por_tipo = {
        "pedido recebido": "pedida",
        "desenho aprovado": "desenho aprovado",
        "sessão": "em sessões",
        "retoque": "finalizada",
    }

    # Aceita somente as quatro etapas que o tatuador pode selecionar.
    if tipo not in etapas_por_tipo:
        return None, tatuagem, "Escolha uma etapa válida para este pedido."

    # Cada registro atualiza individualmente a etapa selecionada pelo tatuador.

    passo = repositorio_passo.criar(
        {
            "tatuagem_id": tatuagem_id,
            "tipo": tipo,
            "data": dados["data"],
            "observacao": dados.get("observacao", ""),
        }
    )
    tatuagem_atualizada = repositorio_tatuagem.atualizar_etapa(
        tatuagem_id, etapas_por_tipo[tipo]
    )
    passo_com_etapa = {**passo, "etapa_atualizada": tatuagem_atualizada["etapa"]}
    return passo_com_etapa, tatuagem_atualizada, None
