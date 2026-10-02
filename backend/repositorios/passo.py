# Mantém os passos em memória enquanto o servidor estiver ligado.
passos = []
proximo_id = 1


# Guarda um passo aceito e associa-o à tatuagem informada.
def criar(dados: dict) -> dict:
    global proximo_id

    passo = {"id": proximo_id, **dados}
    passos.append(passo)
    proximo_id += 1
    return passo


# Busca os passos que formam o histórico de uma tatuagem.
def listar_por_tatuagem(tatuagem_id: int) -> list:
    resultado = []

    for passo in passos:
        if passo["tatuagem_id"] == tatuagem_id:
            resultado.append(passo)

    return resultado


# Apaga todos os registros do histórico de uma tatuagem e informa quantos saíram.
def descartar_por_tatuagem(tatuagem_id: int) -> int:
    quantidade_inicial = len(passos)
    passos[:] = [passo for passo in passos if passo["tatuagem_id"] != tatuagem_id]
    return quantidade_inicial - len(passos)
