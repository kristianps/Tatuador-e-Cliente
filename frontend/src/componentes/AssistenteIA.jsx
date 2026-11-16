import { useEffect, useRef, useState } from "react";

import { enderecoApi } from "../api.js";
import { TIPOS_ACEITOS, lerFoto, reduzirImagem } from "../imagens.js";
import VisualizadorFoto from "./VisualizadorFoto.jsx";

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

// Prepara a conversa para enviar: só a foto mais recente vai junto, as anteriores viram uma observação.
// Assim cada pergunta não reenvia todas as fotos, o que deixaria o envio lento no celular.
function prepararHistorico(historico) {
  const ultimaComFoto = historico.map((fala) => Boolean(fala.imagem)).lastIndexOf(true);
  return historico.slice(-20).map((fala, indice, lista) => {
    const posicaoReal = historico.length - lista.length + indice;
    if (!fala.imagem || posicaoReal === ultimaComFoto) return fala;
    return { papel: fala.papel, texto: `${fala.texto} (a cliente tinha enviado uma foto antes)`.trim() };
  });
}

// Assistente de ideias com IA, dentro da tela de pedido.
// A cliente conversa, envia fotos de referência para a IA comentar e pode anexar uma foto ao pedido.
function AssistenteIA({ aoUsar }) {
  const [aberta, definirAberta] = useState(false);
  // historico guarda a conversa no formato que a API espera: papel, texto e, se houver, a foto.
  const [historico, definirHistorico] = useState([]);
  const [texto, definirTexto] = useState("");
  const [foto, definirFoto] = useState("");
  const [pensando, definirPensando] = useState(false);
  const [erro, definirErro] = useState("");
  const [fotoAberta, definirFotoAberta] = useState("");
  const listaRef = useRef(null);
  const arquivoRef = useRef(null);

  // Mantém a última fala visível dentro da caixa da conversa.
  useEffect(() => {
    if (listaRef.current) listaRef.current.scrollTop = listaRef.current.scrollHeight;
  }, [historico.length, pensando]);

  // Manda a fala da cliente (texto, foto ou os dois) com a conversa, porque a IA não guarda memória entre as chamadas.
  function perguntar(conteudo, fotoDaFala = "") {
    const fala = conteudo.trim();
    if ((!fala && !fotoDaFala) || pensando) return;
    const novaFala = { papel: "cliente", texto: fala, ...(fotoDaFala ? { imagem: fotoDaFala } : {}) };
    const novoHistorico = [...historico, novaFala];
    definirHistorico(novoHistorico);
    definirTexto("");
    definirFoto("");
    definirErro("");
    definirPensando(true);

    chamarIa("/ia/assistente", { historico: prepararHistorico(novoHistorico) })
      .then((dados) => definirHistorico((atual) => [...atual, { papel: "assistente", texto: dados.resposta }]))
      .catch((erroIa) => definirErro(erroIa.message))
      .finally(() => definirPensando(false));
  }

  function enviar(evento) {
    evento.preventDefault();
    perguntar(texto, foto);
  }

  // Lê a foto escolhida e deixa pronta para ir com a próxima fala.
  function escolherFoto(evento) {
    const arquivo = evento.target.files[0];
    evento.target.value = "";
    if (!arquivo) return;
    definirErro("");
    lerFoto(arquivo)
      .then(definirFoto)
      .catch((erroFoto) => definirErro(erroFoto.message));
  }

  // Anexa ao pedido a foto escolhida, junto com um resumo do que a cliente escreveu.
  function usarNoPedido(imagem) {
    const resumo = historico
      .filter((fala) => fala.papel === "cliente" && fala.texto)
      .map((fala) => fala.texto)
      .join("; ")
      .slice(0, 500);
    // Para o pedido, uma versão menor basta: o estúdio usa só como referência.
    reduzirImagem(imagem, 768).then((reduzida) => aoUsar({ imagem: reduzida, ideia: resumo }));
  }

  const conversou = historico.some((fala) => fala.papel === "cliente");

  if (!aberta) {
    return (
      <section className="assistente-ia fechada">
        <div>
          <p className="assistente-selo">Novo · Assistente com IA</p>
          <h2>Não sabe o que tatuar?</h2>
          <p>Converse com a nossa assistente: ela ajuda a escolher a ideia e comenta fotos de referência que você enviar.</p>
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
          Oi! Me conte o que você imagina ou envie uma foto de referência pelo clipe: uma tatuagem que você viu, um desenho ou o local do corpo. Eu ajudo a transformar em uma ideia de tatuagem.
        </li>
        {historico.map((fala, indice) => (
          <li key={indice} className={fala.papel === "cliente" ? "fala-cliente" : "fala-ia"}>
            {fala.imagem && (
              <div className="fala-foto">
                <button type="button" className="mensagem-foto" onClick={() => definirFotoAberta(fala.imagem)}>
                  <img src={fala.imagem} alt="Foto de referência enviada para a assistente" />
                </button>
                <button type="button" className="botao-usar-foto" onClick={() => usarNoPedido(fala.imagem)}>
                  Usar no meu pedido
                </button>
              </div>
            )}
            {fala.texto}
          </li>
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

      {foto && (
        <div className="foto-escolhida foto-escolhida-escura">
          <img src={foto} alt="Foto que será enviada para a assistente" />
          <span>Foto pronta. Escreva algo, se quiser, e toque em Enviar.</span>
          <button type="button" className="botao-secundario" onClick={() => definirFoto("")}>Remover</button>
        </div>
      )}

      {/* Não é um <form>: a assistente fica dentro do formulário do pedido, e formulário dentro de formulário não é permitido. */}
      <div className="assistente-escrever">
        <input ref={arquivoRef} type="file" accept={TIPOS_ACEITOS} hidden onChange={escolherFoto} />
        <button type="button" className="botao-anexar" aria-label="Anexar foto de referência" title="Anexar foto" onClick={() => arquivoRef.current?.click()}>
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M21 11.5l-8.5 8.5a5 5 0 0 1-7-7L14 4.5a3.5 3.5 0 0 1 5 5l-8.5 8.5a2 2 0 0 1-3-3L15 7.5" /></svg>
        </button>
        <textarea
          aria-label="Escreva para a assistente"
          placeholder="Escreva sua ideia…"
          rows={2}
          maxLength={1000}
          value={texto}
          onChange={(evento) => definirTexto(evento.target.value)}
          onKeyDown={(evento) => {
            // No computador, Enter envia; no celular, quebra a linha.
            if (evento.key === "Enter" && !evento.shiftKey && !window.matchMedia("(pointer: coarse)").matches) enviar(evento);
          }}
        />
        <button className="botao-principal" type="button" onClick={enviar} disabled={pensando || (!texto.trim() && !foto)}>Enviar</button>
      </div>

      {fotoAberta && <VisualizadorFoto foto={fotoAberta} aoFechar={() => definirFotoAberta("")} />}
    </section>
  );
}

export default AssistenteIA;
