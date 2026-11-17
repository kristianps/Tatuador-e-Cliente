import json
import time
import unicodedata
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

# Tempo máximo de espera por modelo, e o tempo total para tentar todos os modelos da lista.
# O total fica abaixo do limite de uma função da Vercel; acabou o tempo, entra a resposta de reserva.
TEMPO_POR_MODELO = 12
TEMPO_TOTAL = 25

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
def _post_json(url: str, cabecalhos: dict, corpo: dict, tempo: float) -> Optional[dict]:
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


# Quanto tempo ainda resta antes do prazo; nunca mais que o tempo de um modelo.
def _tempo_restante(prazo: float) -> float:
    return min(TEMPO_POR_MODELO, prazo - time.monotonic())


# Texto pelo Google AI Studio. historico é uma lista de {"papel": "cliente" ou "assistente", "texto": ..., "imagem": ...}.
# Tenta os modelos da lista em ordem e para no primeiro que responder.
def _texto_google(instrucao: str, historico: list, saida_json: bool, prazo: float) -> Optional[str]:
    if not configuracao.GOOGLE_API_KEY:
        return None
    for modelo in configuracao.GOOGLE_MODELOS_TEXTO:
        if _tempo_restante(prazo) < 2:
            return None
        texto = _texto_google_modelo(modelo, instrucao, historico, saida_json, _tempo_restante(prazo))
        if texto:
            return texto
    return None


def _texto_google_modelo(modelo: str, instrucao: str, historico: list, saida_json: bool, tempo: float) -> Optional[str]:
    config = {"temperature": 0.8, "maxOutputTokens": 1024}
    # O modo de raciocínio curto só existe na família Gemini 3 em diante; outros modelos recusariam o pedido.
    if modelo.startswith("gemini-3") or "latest" in modelo:
        config["thinkingConfig"] = {"thinkingLevel": "low"}
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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    resposta = _post_json(url, {"x-goog-api-key": configuracao.GOOGLE_API_KEY}, corpo, tempo)
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
def _texto_openrouter(instrucao: str, historico: list, prazo: float) -> Optional[str]:
    if not configuracao.OPENROUTER_API_KEY or _tempo_restante(prazo) < 2:
        return None
    mensagens = [{"role": "system", "content": instrucao}] + [
        {"role": "assistant" if item["papel"] == "assistente" else "user", "content": _conteudo_openrouter(item)}
        for item in historico
    ]
    # "models" é a lista de reserva da própria OpenRouter: se o primeiro estiver ocupado, ela tenta o seguinte.
    corpo = {"models": configuracao.OPENROUTER_MODELOS_TEXTO[:3], "max_tokens": 1500, "messages": mensagens}
    resposta = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {configuracao.OPENROUTER_API_KEY}"},
        corpo,
        _tempo_restante(prazo),
    )
    try:
        return (resposta["choices"][0]["message"]["content"] or "").strip() or None
    except (TypeError, KeyError, IndexError):
        return None


# Tenta todos os modelos do Google e, se nenhum responder, os da OpenRouter, dentro do tempo total.
def _gerar_texto(instrucao: str, historico: list, saida_json: bool = False) -> Optional[str]:
    prazo = time.monotonic() + TEMPO_TOTAL
    return _texto_google(instrucao, historico, saida_json, prazo) or _texto_openrouter(instrucao, historico, prazo)


# Confere o limite diário da pessoa. Devolve o motivo da recusa, ou None quando ainda pode usar.
def _motivo_limite(usuario: dict, tipo: str) -> Optional[str]:
    if repositorio_ia.contar_uso_recente(usuario["id"], tipo) >= LIMITES_POR_DIA[tipo]:
        return "Você atingiu o limite diário deste recurso de IA. Tente de novo amanhã."
    return None


# Conversa da assistente de ideias. Devolve (resposta, motivo): só um dos dois vem preenchido.
# Sem IA disponível (cotas esgotadas, serviço fora) ou com o limite diário atingido, a conversa
# continua com perguntas-guia prontas, em vez de mostrar erro para a cliente.
def conversar(usuario: dict, historico: list) -> Tuple[Optional[str], Optional[str]]:
    if _motivo_limite(usuario, "conversa"):
        return _resposta_guia(historico), None

    resposta = _gerar_texto(INSTRUCAO_ASSISTENTE, _manter_ultima_imagem(historico))
    if resposta is None:
        print("Aviso: nenhum modelo de IA respondeu; a assistente usou a resposta-guia.")
        return _resposta_guia(historico), None

    repositorio_ia.registrar_uso(usuario["id"], "conversa")
    return resposta, None


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


# O que a assistente precisa saber, na ordem em que pergunta, com palavras que mostram que a cliente já respondeu.
_PERGUNTAS_GUIA = [
    (("fineline", "fine line", "old school", "tradicional", "blackwork", "realis", "aquarela", "geometric",
      "minimalis", "traco fino", "pontilh", "tribal", "neotrad", "lettering", "escrita"),
     "Qual estilo combina mais com você: traço fino (fineline), old school, blackwork, realismo, aquarela ou geométrico?"),
    (("braco", "ombro", "mao", "dedo", "pulso", "costela", "costas", "peito", "nuca", "pescoco", "coxa",
      "perna", "panturrilha", "canela", "tornozelo", " pe ", "barriga", "quadril", "clavicula"),
     "Em que parte do corpo você pensa em fazer?"),
    (("cm", "centimet", "pequen", "medi", "grand", "delicad", "fechament"),
     "Mais ou menos de que tamanho, em centímetros?"),
    (("signific", "homenag", "lembr", "represent", "simboli", "porque", "por que", "memoria"),
     "Ela tem algum significado especial para você? Isso ajuda o tatuador a criar algo único."),
]


# Resposta montada sem IA: comenta a foto, se houver, e pergunta o próximo detalhe que ainda falta.
def _resposta_guia(historico: list) -> str:
    falas = [item for item in historico if item.get("papel") == "cliente"]
    texto = " " + _sem_acento(" ".join(item.get("texto") or "" for item in falas)) + " "
    ultima = falas[-1] if falas else {}

    abertura = "Que legal!"
    if ultima.get("imagem"):
        abertura = "Recebi sua foto de referência, ela vai ajudar muito o tatuador!"

    for palavras, pergunta in _PERGUNTAS_GUIA:
        if not any(palavra in texto for palavra in palavras):
            return f"{abertura} {pergunta}"

    return (
        f"{abertura} Acho que já temos uma boa ideia. Toque em \"Usar esta conversa no meu pedido\" "
        "para levar tudo para o pedido; o tatuador vai transformar sua ideia em desenho."
    )


# Sugere 3 respostas para a conversa de um pedido, do ponto de vista de quem está logado.
# Devolve (sugestoes, encontrada, motivo), como os outros serviços, para a rota escolher o status.
def sugerir_respostas(usuario: dict, tatuagem_id: int) -> Tuple[Optional[list], bool, Optional[str]]:
    tatuagem = repositorio_tatuagem.buscar_por_id(tatuagem_id)
    eh_tatuador = usuario["perfil"] == GRUPO_TATUADOR
    # Mesma regra da conversa: a cliente só mexe nos pedidos dela.
    if tatuagem is None or (not eh_tatuador and tatuagem["cliente_id"] != usuario["id"]):
        return None, False, None

    if _motivo_limite(usuario, "sugestao"):
        return _sugestoes_prontas(eh_tatuador, tatuagem), True, None

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
        return _sugestoes_prontas(eh_tatuador, tatuagem), True, None

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


# Respostas prontas para quando a IA não responde: educadas, sem preço nem data, e de acordo com a etapa.
_SUGESTOES_TATUADOR = {
    "pedida": [
        "Oi! Recebi seu pedido e já vou começar a pensar no desenho.",
        "Você pode me mandar uma foto do local onde quer tatuar?",
        "Tem mais alguma referência que você goste? Pode mandar por aqui.",
    ],
    "desenho aprovado": [
        "Que bom que gostou do desenho! Vamos combinar a primeira sessão?",
        "Lembre de se hidratar e dormir bem antes da sessão.",
        "Qualquer dúvida sobre o desenho, é só me chamar.",
    ],
}
_SUGESTOES_TATUADOR_PADRAO = [
    "Oi! Como está a cicatrização?",
    "Qualquer dúvida, é só me chamar por aqui.",
    "Obrigado pela confiança! Logo te passo as novidades.",
]
_SUGESTOES_CLIENTE = [
    "Oi! Alguma novidade sobre o meu pedido?",
    "Posso mandar mais uma foto de referência?",
    "Qual é o próximo passo?",
]


def _sugestoes_prontas(eh_tatuador: bool, tatuagem: dict) -> list:
    if not eh_tatuador:
        return list(_SUGESTOES_CLIENTE)
    return list(_SUGESTOES_TATUADOR.get(tatuagem.get("etapa"), _SUGESTOES_TATUADOR_PADRAO))
