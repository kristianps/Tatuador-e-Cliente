import json
import urllib.error
import urllib.request
from typing import Optional, Tuple

import configuracao
from repositorios import ia as repositorio_ia
from repositorios import mensagem as repositorio_mensagem
from repositorios import tatuagem as repositorio_tatuagem
from servicos.usuario import GRUPO_TATUADOR

# Quantas vezes cada pessoa pode usar cada recurso em 24 horas.
LIMITES_POR_DIA = {"conversa": 40, "sugestao": 30, "resumo": 20}

# Tempo máximo de espera pela resposta da IA.
TEMPO_TEXTO = 30

INSTRUCAO_ASSISTENTE = """Você é a assistente de criação do PereiraTatto, um estúdio de tatuagem.
Seu papel é ajudar a cliente a escolher uma tatuagem antes de fazer o pedido.
- Responda sempre em português do Brasil, em tom acolhedor e direto, com no máximo 120 palavras.
- Pergunte, aos poucos, o que importa: o significado, o estilo (fineline, old school, blackwork, realismo, aquarela, geométrico), o local do corpo e o tamanho aproximado em centímetros.
- Sugira de 2 a 3 ideias concretas e curtas quando já souber o suficiente.
- Se a cliente enviar uma foto (uma tatuagem de referência, um desenho ou o local do corpo), descreva em poucas palavras o que vê e sugira como adaptar a ideia para tatuagem. Não tente identificar pessoas pela foto.
- Quando a ideia estiver clara, diga que ela pode tocar em "Usar no meu pedido" embaixo da foto, ou descrever a ideia no pedido.
- Você não cria imagens nem desenhos; o desenho final é sempre feito pelo tatuador.
- Não informe preço, prazo ou agenda: isso é combinado com o estúdio.
- Não dê orientação médica; para dúvidas de pele ou saúde, oriente a conversar com o tatuador.
- Use texto simples, sem títulos nem tabelas."""

INSTRUCAO_RESUMO = """Você organiza o pedido de tatuagem de uma cliente para o tatuador do estúdio PereiraTatto.
Leia a conversa entre a cliente e a assistente de ideias e responda só com um objeto JSON com estas chaves:
"estilo": o estilo em poucas palavras (ex.: "fineline", "old school"), ou "" se não foi decidido;
"elementos": lista com até 6 elementos do desenho, cada um em poucas palavras;
"significado": o significado ou a motivação em uma frase curta, ou "";
"cores": "preto e cinza", "colorida" ou uma descrição curta das cores, ou "" se não foi decidido;
"local_corpo": o local do corpo citado, ou "";
"tamanho_cm": o tamanho aproximado em centímetros como número inteiro, ou null;
"pendencias": lista com até 4 perguntas curtas que o tatuador ainda precisa fazer para desenhar.
Use só o que a cliente disse ou aprovou; não invente detalhes. Se ela enviou uma foto de referência, pode citar o que aparece nela.
Escreva em português do Brasil, sem preço, data ou horário."""

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


# Separa um data URL ("data:image/jpeg;base64,AAAA") no tipo da imagem e no conteúdo em base64.
def _partes_da_imagem(data_url: str) -> Tuple[str, str]:
    cabecalho, conteudo = data_url.split(",", 1)
    return cabecalho[len("data:"):].split(";")[0], conteudo


# Só a foto mais recente vai para a IA; as anteriores viram uma observação no texto.
# Assim cada pergunta não reenvia todas as fotos da conversa, o que deixaria a chamada lenta e pesada.
def _manter_ultima_imagem(historico: list) -> list:
    indices = [i for i, item in enumerate(historico) if item.get("imagem")]
    ultima = indices[-1] if indices else None
    resultado = []
    for i, item in enumerate(historico):
        if item.get("imagem") and i != ultima:
            texto = (item.get("texto") or "").strip()
            item = {**item, "imagem": None, "texto": f"{texto} (a cliente tinha enviado uma foto antes)".strip()}
        resultado.append(item)
    return resultado


# Texto pelo Google AI Studio. historico é uma lista de {"papel": "cliente" ou "assistente", "texto": ..., "imagem": ...}.
def _texto_google(instrucao: str, historico: list, saida_json: bool) -> Optional[str]:
    if not configuracao.GOOGLE_API_KEY:
        return None
    config = {"temperature": 0.8, "maxOutputTokens": 1024, "thinkingConfig": {"thinkingLevel": "low"}}
    if saida_json:
        config["responseMimeType"] = "application/json"
        # O limite de saída conta também o raciocínio interno do modelo; com pouco espaço,
        # o JSON vinha cortado no meio. Respostas em JSON ganham mais folga.
        config["maxOutputTokens"] = 4096
    corpo = {
        "systemInstruction": {"parts": [{"text": instrucao}]},
        # O Google chama a IA de "model" e a pessoa de "user".
        "contents": [
            {"role": "model" if item["papel"] == "assistente" else "user", "parts": _partes_google(item)}
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


# Monta as partes de uma fala para o Google: o texto e, se houver, a foto (inlineData = imagem em base64).
def _partes_google(item: dict) -> list:
    partes = []
    if item.get("texto"):
        partes.append({"text": item["texto"]})
    if item.get("imagem"):
        tipo, conteudo = _partes_da_imagem(item["imagem"])
        partes.append({"inlineData": {"mimeType": tipo, "data": conteudo}})
    return partes


# Monta o conteúdo de uma fala para a OpenRouter: texto simples, ou uma lista com texto e imagem.
def _conteudo_openrouter(item: dict):
    if not item.get("imagem"):
        return item["texto"]
    conteudo = [{"type": "image_url", "image_url": {"url": item["imagem"]}}]
    if item.get("texto"):
        conteudo.insert(0, {"type": "text", "text": item["texto"]})
    return conteudo


# Texto pela OpenRouter, usada quando o Google falha.
def _texto_openrouter(instrucao: str, historico: list) -> Optional[str]:
    if not configuracao.OPENROUTER_API_KEY:
        return None
    mensagens = [{"role": "system", "content": instrucao}] + [
        {"role": "assistant" if item["papel"] == "assistente" else "user", "content": _conteudo_openrouter(item)}
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

    resposta = _gerar_texto(INSTRUCAO_ASSISTENTE, _manter_ultima_imagem(historico))
    if resposta is None:
        return None, "A assistente está indisponível agora. Tente de novo em instantes."

    repositorio_ia.registrar_uso(usuario["id"], "conversa")
    return resposta, None


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
    # Mensagem só com foto aparece para a IA como "(enviou uma foto)".
    linhas = [
        f"{'Estúdio' if m['autor_perfil'] == GRUPO_TATUADOR else 'Cliente'} ({m['autor_nome']}): "
        + (m["texto"] or "") + (" (enviou uma foto)" if m.get("imagem") else "")
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


# Lê o objeto que a IA devolveu. Aceita o objeto solto ou dentro de um bloco ```json.
def _ler_objeto_json(texto: Optional[str]) -> dict:
    if not texto:
        return {}
    limpo = texto.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        objeto = json.loads(limpo)
    except ValueError:
        return {}
    return objeto if isinstance(objeto, dict) else {}


def _texto_curto(valor, limite: int) -> str:
    return str(valor).strip()[:limite] if isinstance(valor, (str, int, float)) else ""


def _lista_curta(valor, quantidade: int) -> list:
    if not isinstance(valor, list):
        return []
    itens = [_texto_curto(item, 200) for item in valor]
    return [item for item in itens if item][:quantidade]


# A IA pode errar o formato; aqui cada campo é ajustado ao tamanho e ao tipo que o pedido aceita.
def _normalizar_resumo(bruto: dict) -> dict:
    tamanho = bruto.get("tamanho_cm")
    if isinstance(tamanho, float):
        tamanho = round(tamanho)
    if not isinstance(tamanho, int) or isinstance(tamanho, bool) or not 1 <= tamanho <= 100:
        tamanho = None
    return {
        "estilo": _texto_curto(bruto.get("estilo"), 120),
        "elementos": _lista_curta(bruto.get("elementos"), 6),
        "significado": _texto_curto(bruto.get("significado"), 300),
        "cores": _texto_curto(bruto.get("cores"), 120),
        "pendencias": _lista_curta(bruto.get("pendencias"), 4),
        "local_corpo": _texto_curto(bruto.get("local_corpo"), 120),
        "tamanho_cm": tamanho,
    }


# Transforma a conversa com a assistente num resumo organizado para o tatuador.
# A conversa vai como um texto só, para a IA ler tudo de uma vez e responder uma única vez em JSON.
def resumir_pedido(usuario: dict, historico: list) -> Tuple[Optional[dict], Optional[str]]:
    motivo = _motivo_limite(usuario, "resumo")
    if motivo:
        return None, motivo

    historico = _manter_ultima_imagem(historico)
    linhas = [
        f"{'Cliente' if item['papel'] == 'cliente' else 'Assistente'}: "
        + ((item.get("texto") or "").strip() or "(enviou uma foto)")
        for item in historico
    ]
    foto = next((item["imagem"] for item in reversed(historico) if item.get("imagem")), None)
    pedido = {"papel": "cliente", "texto": "Conversa:\n" + "\n".join(linhas), "imagem": foto}

    resumo = _normalizar_resumo(_ler_objeto_json(_gerar_texto(INSTRUCAO_RESUMO, [pedido], saida_json=True)))
    campos_preenchidos = [resumo["estilo"], resumo["elementos"], resumo["significado"], resumo["cores"]]
    if not any(campos_preenchidos):
        return None, "Não foi possível resumir a conversa agora. Tente de novo em instantes."

    repositorio_ia.registrar_uso(usuario["id"], "resumo")
    return resumo, None
