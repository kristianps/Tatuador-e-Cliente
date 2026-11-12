import json
import urllib.error
import urllib.request
from typing import Optional, Tuple

import configuracao
from repositorios import ia as repositorio_ia
from repositorios import mensagem as repositorio_mensagem
from repositorios import tatuagem as repositorio_tatuagem
from servicos.usuario import GRUPO_TATUADOR

# Quantas vezes cada pessoa pode usar cada recurso em 24 horas. Imagem é o mais caro, por isso o menor limite.
LIMITES_POR_DIA = {"conversa": 40, "imagem": 5, "sugestao": 30}

# Tempo máximo de espera pela resposta da IA. Imagem demora mais que texto.
TEMPO_TEXTO = 30
TEMPO_IMAGEM = 60

INSTRUCAO_ASSISTENTE = """Você é a assistente de criação do PereiraTatto, um estúdio de tatuagem.
Seu papel é ajudar a cliente a escolher uma tatuagem antes de fazer o pedido.
- Responda sempre em português do Brasil, em tom acolhedor e direto, com no máximo 120 palavras.
- Pergunte, aos poucos, o que importa: o significado, o estilo (fineline, old school, blackwork, realismo, aquarela, geométrico), o local do corpo e o tamanho aproximado em centímetros.
- Sugira de 2 a 3 ideias concretas e curtas quando já souber o suficiente.
- Quando a ideia estiver clara, diga que ela pode tocar em "Gerar imagem" para ver um rascunho.
- Não informe preço, prazo ou agenda: isso é combinado com o estúdio.
- Não dê orientação médica; para dúvidas de pele ou saúde, oriente a conversar com o tatuador.
- Use texto simples, sem títulos nem tabelas."""

INSTRUCAO_IMAGEM = """Crie o desenho de uma tatuagem, como uma folha de flash de estúdio:
traço limpo, fundo branco liso, desenho centralizado, sem pele, sem pessoas, sem texto escrito e sem marca d'água.
Siga o estilo e os elementos pedidos. Ideia da cliente, a partir da conversa com a assistente:"""

INSTRUCAO_SUGESTOES = """Você ajuda {quem} de um estúdio de tatuagem a responder mensagens.
Com base no pedido e nas últimas mensagens, escreva 3 respostas curtas e diferentes que {quem} poderia enviar agora.
Cada resposta tem no máximo 160 caracteres, em português do Brasil, educada e natural, sem inventar preço, data ou horário.
Responda só com uma lista JSON de 3 textos, por exemplo: ["...", "...", "..."]"""


# Envia um pedido HTTP com corpo JSON e devolve a resposta já convertida.
# urllib vem com o Python, então não precisa de biblioteca nova no requirements.
def _post_json(url: str, cabecalhos: dict, corpo: dict, tempo: int) -> Optional[dict]:
    pedido = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json", **cabecalhos},
    )
    try:
        with urllib.request.urlopen(pedido, timeout=tempo) as resposta:
            return json.loads(resposta.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as erro:
        # Fica só no log da Vercel; a chave nunca aparece aqui, porque vai no cabeçalho, não na URL.
        codigo = getattr(erro, "code", "")
        print(f"Aviso: falha ao chamar a IA em {url.split('?')[0]}: {type(erro).__name__} {codigo}")
        return None


# Texto pelo Google AI Studio. historico é uma lista de {"papel": "cliente" ou "assistente", "texto": ...}.
def _texto_google(instrucao: str, historico: list, saida_json: bool) -> Optional[str]:
    if not configuracao.GOOGLE_API_KEY:
        return None
    config = {"temperature": 0.8, "maxOutputTokens": 1024, "thinkingConfig": {"thinkingLevel": "low"}}
    if saida_json:
        config["responseMimeType"] = "application/json"
    corpo = {
        "systemInstruction": {"parts": [{"text": instrucao}]},
        # O Google chama a IA de "model" e a pessoa de "user".
        "contents": [
            {"role": "model" if item["papel"] == "assistente" else "user", "parts": [{"text": item["texto"]}]}
            for item in historico
        ],
        "generationConfig": config,
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{configuracao.GOOGLE_MODELO_TEXTO}:generateContent"
    resposta = _post_json(url, {"x-goog-api-key": configuracao.GOOGLE_API_KEY}, corpo, TEMPO_TEXTO)
    try:
        partes = resposta["candidates"][0]["content"]["parts"]
        # As partes marcadas como "thought" são o raciocínio interno do modelo, não a resposta.
        texto = "".join(parte.get("text", "") for parte in partes if not parte.get("thought")).strip()
        return texto or None
    except (TypeError, KeyError, IndexError):
        return None


# Texto pela OpenRouter, usada quando o Google falha.
def _texto_openrouter(instrucao: str, historico: list) -> Optional[str]:
    if not configuracao.OPENROUTER_API_KEY:
        return None
    mensagens = [{"role": "system", "content": instrucao}] + [
        {"role": "assistant" if item["papel"] == "assistente" else "user", "content": item["texto"]}
        for item in historico
    ]
    corpo = {"model": configuracao.OPENROUTER_MODELO_TEXTO, "max_tokens": 800, "messages": mensagens}
    resposta = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {configuracao.OPENROUTER_API_KEY}"},
        corpo,
        TEMPO_TEXTO,
    )
    try:
        return (resposta["choices"][0]["message"]["content"] or "").strip() or None
    except (TypeError, KeyError, IndexError):
        return None


# Tenta o Google e, se ele falhar, a OpenRouter.
def _gerar_texto(instrucao: str, historico: list, saida_json: bool = False) -> Optional[str]:
    return _texto_google(instrucao, historico, saida_json) or _texto_openrouter(instrucao, historico)


# Imagem pela OpenRouter, que devolve a imagem pronta como data URL.
def _imagem_openrouter(prompt: str) -> Optional[str]:
    if not configuracao.OPENROUTER_API_KEY:
        return None
    corpo = {
        "model": configuracao.OPENROUTER_MODELO_IMAGEM,
        # modalities pede ao modelo que responda com imagem, além de texto.
        "modalities": ["image", "text"],
        "messages": [{"role": "user", "content": prompt}],
    }
    resposta = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {configuracao.OPENROUTER_API_KEY}"},
        corpo,
        TEMPO_IMAGEM,
    )
    try:
        url = resposta["choices"][0]["message"]["images"][0]["image_url"]["url"]
        return url if url.startswith("data:image/") else None
    except (TypeError, KeyError, IndexError):
        return None


# Imagem pelo Google, que devolve o tipo e o conteúdo em base64; aqui viram um data URL.
def _imagem_google(prompt: str) -> Optional[str]:
    if not configuracao.GOOGLE_API_KEY:
        return None
    corpo = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{configuracao.GOOGLE_MODELO_IMAGEM}:generateContent"
    resposta = _post_json(url, {"x-goog-api-key": configuracao.GOOGLE_API_KEY}, corpo, TEMPO_IMAGEM)
    try:
        for parte in resposta["candidates"][0]["content"]["parts"]:
            if "inlineData" in parte:
                return f"data:{parte['inlineData']['mimeType']};base64,{parte['inlineData']['data']}"
    except (TypeError, KeyError, IndexError):
        pass
    return None


# Confere o limite diário da pessoa. Devolve o motivo da recusa, ou None quando ainda pode usar.
def _motivo_limite(usuario: dict, tipo: str) -> Optional[str]:
    if repositorio_ia.contar_uso_recente(usuario["id"], tipo) >= LIMITES_POR_DIA[tipo]:
        return "Você atingiu o limite diário deste recurso de IA. Tente de novo amanhã."
    return None


# Conversa da assistente de ideias. Devolve (resposta, motivo): só um dos dois vem preenchido.
def conversar(usuario: dict, historico: list) -> Tuple[Optional[str], Optional[str]]:
    motivo = _motivo_limite(usuario, "conversa")
    if motivo:
        return None, motivo

    resposta = _gerar_texto(INSTRUCAO_ASSISTENTE, historico)
    if resposta is None:
        return None, "A assistente está indisponível agora. Tente de novo em instantes."

    repositorio_ia.registrar_uso(usuario["id"], "conversa")
    return resposta, None


# Gera o rascunho da tatuagem a partir do que a cliente disse na conversa com a assistente.
def gerar_imagem(usuario: dict, historico: list) -> Tuple[Optional[str], Optional[str]]:
    motivo = _motivo_limite(usuario, "imagem")
    if motivo:
        return None, motivo

    # Junta as falas da cliente e a última sugestão da assistente, que já resume a ideia.
    falas_cliente = [item["texto"] for item in historico if item["papel"] == "cliente"]
    sugestoes = [item["texto"] for item in historico if item["papel"] == "assistente"]
    ideia = "\n".join(falas_cliente[-6:])
    if sugestoes:
        ideia += f"\nÚltima sugestão da assistente: {sugestoes[-1]}"
    prompt = f"{INSTRUCAO_IMAGEM}\n{ideia}"

    imagem = _imagem_openrouter(prompt) or _imagem_google(prompt)
    if imagem is None:
        return None, "A geração de imagem está indisponível agora. A conversa com a assistente continua funcionando."

    repositorio_ia.registrar_uso(usuario["id"], "imagem")
    return imagem, None


# Sugere 3 respostas para a conversa de um pedido, do ponto de vista de quem está logado.
# Devolve (sugestoes, encontrada, motivo), como os outros serviços, para a rota escolher o status.
def sugerir_respostas(usuario: dict, tatuagem_id: int) -> Tuple[Optional[list], bool, Optional[str]]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    eh_tatuador = usuario["perfil"] == GRUPO_TATUADOR
    # Mesma regra da conversa: a cliente só mexe nos pedidos dela.
    if tatuagem is None or (not eh_tatuador and tatuagem["cliente_id"] != usuario["id"]):
        return None, False, None

    motivo = _motivo_limite(usuario, "sugestao")
    if motivo:
        return None, True, motivo

    ultimas = repositorio_mensagem.listar_por_tatuagem(tatuagem_id)[-12:]
    linhas = [
        f"{'Estúdio' if m['autor_perfil'] == GRUPO_TATUADOR else 'Cliente'} ({m['autor_nome']}): {m['texto']}"
        for m in ultimas
    ]
    contexto = (
        f"Pedido: {tatuagem['ideia']}\n"
        f"Local: {tatuagem['local_corpo']}"
        + (f", {tatuagem['tamanho_cm']} cm" if tatuagem.get("tamanho_cm") else "")
        + f"\nEtapa atual: {tatuagem['etapa']}\n\n"
        + ("Últimas mensagens:\n" + "\n".join(linhas) if linhas else "Ainda não há mensagens; sugira como começar a conversa.")
    )
    quem = "o tatuador" if eh_tatuador else "a cliente"
    texto = _gerar_texto(INSTRUCAO_SUGESTOES.format(quem=quem), [{"papel": "cliente", "texto": contexto}], saida_json=True)

    sugestoes = _ler_lista_json(texto)
    if not sugestoes:
        return None, True, "Não foi possível sugerir respostas agora. Tente de novo em instantes."

    repositorio_ia.registrar_uso(usuario["id"], "sugestao")
    return sugestoes, True, None


# Lê a lista de textos que a IA devolveu. Aceita a lista solta ou dentro de um bloco ```json.
def _ler_lista_json(texto: Optional[str]) -> list:
    if not texto:
        return []
    limpo = texto.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        lista = json.loads(limpo)
    except ValueError:
        return []
    if not isinstance(lista, list):
        return []
    return [str(item).strip()[:300] for item in lista if str(item).strip()][:3]
