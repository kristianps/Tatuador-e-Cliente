import { useEffect, useRef, useState } from "react";

import { enderecoApi } from "../api.js";

// De quanto em quanto tempo a conversa pergunta à API se chegou mensagem nova.
// A API roda em funções sem servidor da Vercel, que não mantêm conexão aberta,
// então a tela consulta de tempos em tempos (polling) para parecer instantânea.
const INTERVALO_CONSULTA_MS = 3000;

// Monta os cabeçalhos com o token do login, que diz à API quem está escrevendo.
function cabecalhosComToken(extras = {}) {
  const token = localStorage.getItem("pereiratatto-token");
  return token ? { ...extras, Authorization: `Bearer ${token}` } : extras;
}

// Mostra só a hora para mensagens de hoje e a data junto para as mais antigas.
function formatarHorario(valor) {
  const data = new Date(valor);
  const hora = data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  const ehHoje = data.toDateString() === new Date().toDateString();
  return ehHoje ? hora : `${data.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })} ${hora}`;
}

// Junta mensagens novas às que já estão na tela, sem repetir e em ordem de envio.
// Uma mesma mensagem pode chegar duas vezes: pela resposta do envio e pela consulta seguinte.
function juntarMensagens(atuais, novas) {
  const porId = new Map(atuais.map((mensagem) => [mensagem.id, mensagem]));
  novas.forEach((mensagem) => porId.set(mensagem.id, mensagem));
  return [...porId.values()].sort((a, b) => a.id - b.id);
}

// Conversa de um pedido entre a cliente e o tatuador, usada em Minhas tatuagens e na Ficha.
function Conversa({ tatuagemId, usuario, titulo, aoLer }) {
  const [mensagens, definirMensagens] = useState([]);
  const [texto, definirTexto] = useState("");
  const [estado, definirEstado] = useState("carregando");
  const [erro, definirErro] = useState("");
  const [enviando, definirEnviando] = useState(false);
  // useRef guarda um valor que sobrevive entre renderizações sem redesenhar a tela.
  const ultimoIdRef = useRef(0);
  // Até qual mensagem já avisamos a API que foi lida, para não repetir o aviso sem necessidade.
  const lidaAteRef = useRef(0);
  const aoLerRef = useRef(aoLer);
  aoLerRef.current = aoLer;
  const listaRef = useRef(null);

  // Conta para a API que a pessoa viu a conversa até a última mensagem na tela.
  // Só marca com a aba visível: mensagem que chegou com a aba escondida continua como não lida.
  function marcarComoLidas() {
    const ateId = ultimoIdRef.current;
    if (document.hidden || ateId <= lidaAteRef.current) return;
    lidaAteRef.current = ateId;

    fetch(`${enderecoApi}/tatuagens/${tatuagemId}/mensagens/lidas`, {
      method: "POST",
      headers: cabecalhosComToken({ "Content-Type": "application/json" }),
      body: JSON.stringify({ ate_id: ateId }),
    })
      .then((resposta) => {
        if (!resposta.ok) throw new Error("Falha ao marcar como lida.");
        // Atualiza na hora os contadores das abas, sem esperar a próxima consulta.
        if (aoLerRef.current) aoLerRef.current();
      })
      // Se falhar, tenta de novo na próxima consulta.
      .catch(() => {
        lidaAteRef.current = 0;
      });
  }

  // Guarda as novas mensagens e lembra o maior id, para a próxima consulta pedir só o que vier depois.
  function receberMensagens(novas) {
    if (novas.length === 0) return;
    ultimoIdRef.current = Math.max(ultimoIdRef.current, ...novas.map((mensagem) => mensagem.id));
    definirMensagens((atuais) => juntarMensagens(atuais, novas));
  }

  // Carrega a conversa ao abrir o pedido e repete a consulta enquanto ele estiver aberto.
  useEffect(() => {
    let ativo = true;
    let consultando = false;
    ultimoIdRef.current = 0;
    lidaAteRef.current = 0;
    definirMensagens([]);
    definirEstado("carregando");
    definirErro("");

    function consultar() {
      // Com a aba escondida ninguém está lendo; pular a consulta poupa requisições à API.
      if (consultando || document.hidden) return;
      consultando = true;

      fetch(`${enderecoApi}/tatuagens/${tatuagemId}/mensagens?depois_de=${ultimoIdRef.current}`, {
        headers: cabecalhosComToken(),
      })
        .then((resposta) => {
          if (!resposta.ok) throw new Error("Não foi possível carregar a conversa.");
          return resposta.json();
        })
        .then((novas) => {
          if (!ativo) return;
          receberMensagens(novas);
          definirEstado("pronto");
          definirErro("");
          marcarComoLidas();
        })
        .catch((erroBusca) => {
          if (!ativo) return;
          definirErro(erroBusca.message);
          definirEstado((anterior) => (anterior === "carregando" ? "erro" : anterior));
        })
        .finally(() => {
          consultando = false;
        });
    }

    consultar();
    const intervalo = window.setInterval(consultar, INTERVALO_CONSULTA_MS);
    // Ao voltar para a aba, busca na hora em vez de esperar o próximo intervalo.
    document.addEventListener("visibilitychange", consultar);

    return () => {
      ativo = false;
      window.clearInterval(intervalo);
      document.removeEventListener("visibilitychange", consultar);
    };
  }, [tatuagemId]);

  // Rola só a caixa da conversa até a última mensagem, sem mexer na rolagem da página.
  useEffect(() => {
    const lista = listaRef.current;
    if (lista) lista.scrollTop = lista.scrollHeight;
  }, [mensagens.length]);

  // Envia o texto digitado e coloca a mensagem na tela assim que a API confirma.
  function enviar(evento) {
    evento.preventDefault();
    const conteudo = texto.trim();
    if (!conteudo || enviando) return;

    definirEnviando(true);
    definirErro("");

    fetch(`${enderecoApi}/tatuagens/${tatuagemId}/mensagens`, {
      method: "POST",
      headers: cabecalhosComToken({ "Content-Type": "application/json" }),
      body: JSON.stringify({ texto: conteudo }),
    })
      .then((resposta) => {
        if (!resposta.ok) throw new Error("Não foi possível enviar a mensagem. Tente novamente.");
        return resposta.json();
      })
      .then((mensagem) => {
        receberMensagens([mensagem]);
        definirTexto("");
      })
      .catch((erroEnvio) => definirErro(erroEnvio.message))
      .finally(() => definirEnviando(false));
  }

  // No computador, Enter envia e Shift + Enter quebra a linha. No celular, como no WhatsApp,
  // a tecla Enter do teclado quebra a linha e o envio é pelo botão, para não mandar mensagem pela metade.
  function aoDigitar(evento) {
    const ehToque = window.matchMedia("(pointer: coarse)").matches;
    if (evento.key === "Enter" && !evento.shiftKey && !ehToque) enviar(evento);
  }

  return (
    <section className="conversa" aria-label="Conversa sobre o pedido">
      <div className="conversa-cabecalho">
        <h2>{titulo || "Conversa"}</h2>
        <p>{usuario.perfil === "cliente" ? "Fale com o estúdio sobre este pedido." : "Fale com a cliente sobre este pedido."}</p>
      </div>

      {/* aria-live avisa leitores de tela quando chega mensagem nova. */}
      <ol className="conversa-mensagens" ref={listaRef} aria-live="polite">
        {estado === "carregando" && <li className="conversa-aviso">Carregando conversa…</li>}
        {estado === "pronto" && mensagens.length === 0 && (
          <li className="conversa-aviso">Nenhuma mensagem ainda. Envie uma observação ou dúvida.</li>
        )}
        {mensagens.map((mensagem) => {
          const propria = mensagem.autor_id === usuario.id;
          return (
            <li className={propria ? "mensagem propria" : "mensagem"} key={mensagem.id}>
              {!propria && (
                <p className="mensagem-autor">
                  {mensagem.autor_nome} · {mensagem.autor_perfil === "tatuador" ? "Estúdio" : "Cliente"}
                </p>
              )}
              <p className="mensagem-texto">{mensagem.texto}</p>
              <time dateTime={mensagem.criada_em}>{formatarHorario(mensagem.criada_em)}</time>
            </li>
          );
        })}
      </ol>

      {erro && <p className="aviso erro" role="alert">{erro}</p>}

      <form className="conversa-formulario" onSubmit={enviar}>
        <textarea
          aria-label="Escrever mensagem"
          placeholder="Escreva uma mensagem…"
          rows={1}
          maxLength={1000}
          value={texto}
          onChange={(evento) => definirTexto(evento.target.value)}
          onKeyDown={aoDigitar}
        />
        <button className="botao-principal" type="submit" disabled={enviando || !texto.trim()}>
          {enviando ? "Enviando…" : "Enviar"}
        </button>
      </form>
    </section>
  );
}

export default Conversa;
