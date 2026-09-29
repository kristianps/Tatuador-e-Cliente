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
