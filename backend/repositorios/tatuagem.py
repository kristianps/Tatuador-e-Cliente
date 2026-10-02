from typing import Optional

# Mantém os pedidos em memória enquanto o servidor estiver ligado.
tatuagens = []
proximo_id = 1


# Guarda um novo pedido e entrega seu identificador para as próximas consultas.
def criar(dados: dict) -> dict:
    global proximo_id

    tatuagem = {"id": proximo_id, **dados, "etapa": "pedida"}
    tatuagens.append(tatuagem)
    proximo_id += 1
    return tatuagem


# Procura uma tatuagem pelo identificador e retorna None quando não existe.
def buscar_por_id(tatuagem_id: int) -> Optional[dict]:
    for tatuagem in tatuagens:
        if tatuagem["id"] == tatuagem_id:
            return tatuagem
    return None


# Filtra a lista em memória pelos critérios enviados pela agenda ou pela cliente.
def listar(etapa: Optional[str] = None, cliente_id: Optional[int] = None) -> list:
    resultado = []

    for tatuagem in tatuagens:
        combina_etapa = etapa is None or tatuagem["etapa"] == etapa
        combina_cliente = cliente_id is None or tatuagem["cliente_id"] == cliente_id
        if combina_etapa and combina_cliente:
            resultado.append(tatuagem)

    return resultado


# Atualiza a etapa da tatuagem depois que o serviço aceita um passo.
def atualizar_etapa(tatuagem_id: int, nova_etapa: str) -> Optional[dict]:
    tatuagem = buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None

    tatuagem["etapa"] = nova_etapa
    return tatuagem


# Remove um pedido pelo identificador sem alterar os identificadores dos demais.
def descartar(tatuagem_id: int) -> Optional[dict]:
    tatuagem = buscar_por_id(tatuagem_id)
    if tatuagem is None:
        return None

    tatuagens.remove(tatuagem)
    return tatuagem
