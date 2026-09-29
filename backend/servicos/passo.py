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


# Confere a regra e devolve uma tupla com passo, tatuagem e motivo para a rota escolher o status.
def registrar_passo(
    tatuagem_id: int, dados: dict
) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None, None, None

    tipo = dados["tipo"]
    etapa_atual = tatuagem["etapa"]
    etapas_por_tipo = {
        "desenho aprovado": "desenho aprovado",
        "sessão": "em sessões",
        "retoque": "finalizada",
    }

    # Recusa tipos fora dos três passos que a cartilha descreve.
    if tipo not in etapas_por_tipo:
        return None, tatuagem, "O tipo deve ser desenho aprovado, sessão ou retoque."

    # Garante que o desenho seja o primeiro passo da sequência.
    if tipo == "desenho aprovado" and etapa_atual != "pedida":
        return None, tatuagem, "O desenho só pode ser aprovado quando a tatuagem está pedida."

    # Permite uma ou mais sessões, mas exige aprovação do desenho antes da primeira.
    if tipo == "sessão" and etapa_atual not in ["desenho aprovado", "em sessões"]:
        return None, tatuagem, "A sessão só pode ser registrada depois da aprovação do desenho."

    # Exige ao menos uma sessão; a cartilha não define um campo para registrar a cicatrização.
    # Por isso, o tatuador confirma a cicatrização antes de enviar este passo.
    if tipo == "retoque" and etapa_atual != "em sessões":
        return None, tatuagem, "O retoque só pode ser registrado depois de pelo menos uma sessão."

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
