import { useEffect, useRef, useState } from "react";

import { enderecoApi } from "../api.js";

// Ideias prontas para a cliente começar a conversa com um toque.
const sugestoesIniciais = [
  "Quero algo pequeno e delicado",
  "Uma homenagem a alguém especial",
  "Inspirada na natureza",
  "Estilo old school colorido",
];

function cabecalhosComToken() {
  const token = localStorage.getItem("pereiratatto-token");
  return { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

// Envia para uma rota de IA e devolve o JSON; em erro, usa a mensagem que a API mandou.
function chamarIa(caminho, corpo) {
  return fetch(`${enderecoApi}${caminho}`, { method: "POST", headers: cabecalhosComToken(), body: JSON.stringify(corpo) })
    .then(async (resposta) => {
      const dados = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(typeof dados.detail === "string" ? dados.detail : "A assistente não respondeu. Tente de novo.");
      return dados;
    });
}

// Reduz a imagem para no máximo 768 px e converte para JPEG antes de anexar ao pedido.
// A imagem original da IA pode passar de 1 MB; assim o pedido fica leve para enviar e guardar.
// canvas é uma área de desenho do navegador: a imagem é desenhada menor e exportada de novo.
function reduzirImagem(dataUrl, ladoMaximo = 768) {
  return new Promise((resolver) => {
    const imagem = new Image();
    imagem.onload = () => {
      const escala = Math.min(1, ladoMaximo / Math.max(imagem.width, imagem.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(imagem.width * escala);
      canvas.height = Math.round(imagem.height * escala);
      const contexto = canvas.getContext("2d");
      // Fundo branco: o JPEG não tem transparência.
      contexto.fillStyle = "#ffffff";
      contexto.fillRect(0, 0, canvas.width, canvas.height);
      contexto.drawImage(imagem, 0, 0, canvas.width, canvas.height);
      resolver(canvas.toDataURL("image/jpeg", 0.85));
    };
    // Se não der para reduzir, segue com a original.
    imagem.onerror = () => resolver(dataUrl);
    imagem.src = dataUrl;
  });
}

// Assistente de ideias com IA, dentro da tela de pedido.
// A cliente conversa, gera um rascunho da tatuagem e pode anexá-lo ao pedido.
function AssistenteIA({ aoUsar }) {
  const [aberta, definirAberta] = useState(false);
  // historico guarda a conversa no formato que a API espera: papel e texto.
  const [historico, definirHistorico] = useState([]);
  const [texto, definirTexto] = useState("");
  const [pensando, definirPensando] = useState(false);
  const [erro, definirErro] = useState("");
  const [imagem, definirImagem] = useState("");
  const [gerandoImagem, definirGerandoImagem] = useState(false);
  const [erroImagem, definirErroImagem] = useState("");
  const listaRef = useRef(null);

  // Mantém a última fala visível dentro da caixa da conversa.
  useEffect(() => {
    if (listaRef.current) listaRef.current.scrollTop = listaRef.current.scrollHeight;
  }, [historico.length, pensando]);

  // Manda a fala da cliente com a conversa inteira, porque a IA não guarda memória entre as chamadas.
  function perguntar(conteudo) {
    const fala = conteudo.trim();
    if (!fala || pensando) return;
    const novoHistorico = [...historico, { papel: "cliente", texto: fala }];
    definirHistorico(novoHistorico);
    definirTexto("");
    definirErro("");
    definirPensando(true);

    chamarIa("/ia/assistente", { historico: novoHistorico.slice(-20) })
      .then((dados) => definirHistorico((atual) => [...atual, { papel: "assistente", texto: dados.resposta }]))
      .catch((erroIa) => definirErro(erroIa.message))
      .finally(() => definirPensando(false));
  }

  function enviar(evento) {
    evento.preventDefault();
    perguntar(texto);
  }

  // Pede o rascunho da tatuagem com base no que já foi conversado.
  function gerarImagem() {
    definirGerandoImagem(true);
    definirErroImagem("");
    chamarIa("/ia/imagem", { historico: historico.slice(-20) })
      .then((dados) => definirImagem(dados.imagem))
      .catch((erroIa) => definirErroImagem(erroIa.message))
      .finally(() => definirGerandoImagem(false));
  }

  // Anexa o rascunho ao pedido, junto com um resumo do que a cliente pediu.
  function usarNoPedido() {
    const resumo = historico
      .filter((fala) => fala.papel === "cliente")
      .map((fala) => fala.texto)
      .join("; ")
      .slice(0, 500);
    reduzirImagem(imagem).then((reduzida) => aoUsar({ imagem: reduzida, ideia: resumo }));
  }

  const conversou = historico.some((fala) => fala.papel === "cliente");

  if (!aberta) {
    return (
      <section className="assistente-ia fechada">
        <div>
          <p className="assistente-selo">Novo · Assistente com IA</p>
          <h2>Não sabe o que tatuar?</h2>
          <p>Converse com a nossa assistente: ela ajuda a escolher a ideia e cria um rascunho do desenho.</p>
        </div>
        <button className="botao-principal" type="button" onClick={() => definirAberta(true)}>
          Criar com a IA
        </button>
      </section>
    );
  }

  return (
    <section className="assistente-ia" aria-label="Assistente de ideias com IA">
      <div className="assistente-topo">
        <div>
          <p className="assistente-selo">Assistente com IA</p>
          <h2>Vamos criar sua ideia</h2>
        </div>
        <button className="botao-secundario" type="button" onClick={() => definirAberta(false)}>Fechar</button>
      </div>

      <ol className="assistente-falas" ref={listaRef} aria-live="polite">
        <li className="fala-ia">
          Oi! Me conte o que você imagina: um significado, um estilo, um elemento que você gosta. Eu ajudo a transformar em uma ideia de tatuagem.
        </li>
        {historico.map((fala, indice) => (
          <li key={indice} className={fala.papel === "cliente" ? "fala-cliente" : "fala-ia"}>{fala.texto}</li>
        ))}
        {pensando && <li className="fala-ia pensando">Pensando<span aria-hidden="true">…</span></li>}
      </ol>

      {!conversou && (
        <div className="assistente-atalhos">
          {sugestoesIniciais.map((sugestao) => (
            <button key={sugestao} type="button" className="atalho-ia" onClick={() => perguntar(sugestao)}>{sugestao}</button>
          ))}
        </div>
      )}

      {erro && <p className="aviso erro" role="alert">{erro}</p>}

      {/* Não é um <form>: a assistente fica dentro do formulário do pedido, e formulário dentro de formulário não é permitido. */}
      <div className="assistente-escrever">
        <textarea
          aria-label="Escreva para a assistente"
          placeholder="Ex.: quero um girassol pequeno no pulso…"
          rows={2}
          maxLength={1000}
          value={texto}
          onChange={(evento) => definirTexto(evento.target.value)}
          onKeyDown={(evento) => {
            // No computador, Enter envia; no celular, quebra a linha.
            if (evento.key === "Enter" && !evento.shiftKey && !window.matchMedia("(pointer: coarse)").matches) enviar(evento);
          }}
        />
        <button className="botao-principal" type="button" onClick={enviar} disabled={pensando || !texto.trim()}>Enviar</button>
      </div>

      <div className="assistente-imagem">
        <button className="botao-secundario" type="button" onClick={gerarImagem} disabled={!conversou || gerandoImagem || pensando}>
          {gerandoImagem ? "Desenhando… leva alguns segundos" : imagem ? "Gerar outra imagem" : "Gerar imagem da ideia"}
        </button>
        {!conversou && <p className="ajuda-campo">Conte sua ideia primeiro para liberar a imagem.</p>}
        {erroImagem && <p className="aviso erro" role="alert">{erroImagem}</p>}
        {imagem && (
          <figure className="rascunho-ia">
            <img src={imagem} alt="Rascunho de tatuagem criado pela IA a partir da sua ideia" />
            <figcaption>
              Rascunho criado pela IA. O tatuador usa como referência e faz o desenho final.
            </figcaption>
            <button className="botao-principal" type="button" onClick={usarNoPedido}>Usar no meu pedido</button>
          </figure>
        )}
      </div>
    </section>
  );
}

export default AssistenteIA;
