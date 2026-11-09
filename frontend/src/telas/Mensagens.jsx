import { useEffect, useState } from "react";

import { enderecoApi } from "../api.js";
import Conversa from "../componentes/Conversa.jsx";
import { pedirPermissaoNotificacao, permissaoNotificacao } from "../notificacoes.js";

// Aba de mensagens: a lista de conversas (uma por pedido) e a conversa escolhida, como num aplicativo de mensagens.
function Mensagens({ usuario, pendentes, conversaId, aoSelecionar, aoLer }) {
  const [tatuagens, definirTatuagens] = useState([]);
  const [estado, definirEstado] = useState("carregando");
  const [erro, definirErro] = useState("");
  const [permissao, definirPermissao] = useState(permissaoNotificacao());
  const ehCliente = usuario.perfil === "cliente";

  // Carrega os pedidos que têm conversa e recarrega de tempos em tempos para incluir pedidos novos.
  useEffect(() => {
    let ativo = true;

    function carregar() {
      const token = localStorage.getItem("pereiratatto-token");
      const filtro = ehCliente ? `?cliente_id=${usuario.id}` : "";
      fetch(`${enderecoApi}/tatuagens${filtro}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((resposta) => {
          if (!resposta.ok) throw new Error("Não foi possível carregar as conversas.");
          return resposta.json();
        })
        .then((lista) => {
          if (!ativo) return;
          definirTatuagens(lista);
          definirEstado("pronto");
        })
        .catch((erroBusca) => {
          if (!ativo) return;
          definirErro(erroBusca.message);
          definirEstado((anterior) => (anterior === "carregando" ? "erro" : anterior));
        });
    }

    carregar();
    const intervalo = window.setInterval(carregar, 15000);
    return () => {
      ativo = false;
      window.clearInterval(intervalo);
    };
  }, [ehCliente, usuario.id]);

  // Liga o aviso do navegador depois do clique, como os navegadores exigem.
  function ativarNotificacoes() {
    pedirPermissaoNotificacao().then(definirPermissao);
  }

  // Map deixa achar as não lidas de cada pedido pelo id, sem percorrer a lista toda.
  const naoLidasPorPedido = new Map(pendentes.map((item) => [item.tatuagem_id, item]));

  // Conversas com mensagem nova aparecem primeiro, da mais recente para a mais antiga; depois, os pedidos mais novos.
  const ordenadas = [...tatuagens].sort((a, b) => {
    const ultimaA = naoLidasPorPedido.get(a.id)?.ultima_id || 0;
    const ultimaB = naoLidasPorPedido.get(b.id)?.ultima_id || 0;
    return ultimaB - ultimaA || b.id - a.id;
  });

  const selecionada = tatuagens.find((tatuagem) => tatuagem.id === conversaId) || null;
  // A cliente vê a ideia do pedido; o tatuador vê também o número, que é como o estúdio organiza a agenda.
  const tituloDe = (tatuagem) => (ehCliente ? tatuagem.ideia : `Pedido nº ${tatuagem.id} · ${tatuagem.ideia}`);

  if (estado === "carregando") return <p className="estado-tela">Carregando conversas…</p>;
  if (estado === "erro") return <p className="aviso erro" role="alert">{erro}</p>;

  return (
    <section className="painel painel-mensagens">
      <p className="sobretitulo">CONVERSAS</p>
      <h1>Mensagens</h1>
      <p className="introducao">
        {ehCliente ? "Converse com o estúdio sobre cada pedido." : "Converse com cada cliente sobre o pedido dela."}
      </p>

      {permissao === "default" && (
        <div className="aviso-notificacoes">
          <p>Receba um aviso no navegador quando chegar mensagem nova, mesmo em outra aba.</p>
          <button className="botao-secundario" type="button" onClick={ativarNotificacoes}>Ativar notificações</button>
        </div>
      )}

      {tatuagens.length === 0 ? (
        <div className="estado-vazio">
          {ehCliente ? "Faça um pedido para conversar com o estúdio." : "Ainda não há pedidos para conversar."}
        </div>
      ) : (
        <div className={selecionada ? "area-mensagens com-conversa" : "area-mensagens"}>
          <ul className="lista-conversas" aria-label="Conversas">
            {ordenadas.map((tatuagem) => {
              const pendente = naoLidasPorPedido.get(tatuagem.id);
              return (
                <li key={tatuagem.id}>
                  <button
                    type="button"
                    className={tatuagem.id === conversaId ? "item-conversa ativa" : "item-conversa"}
                    aria-current={tatuagem.id === conversaId ? "true" : undefined}
                    onClick={() => aoSelecionar(tatuagem.id)}
                  >
                    <span className="item-conversa-texto">
                      <strong>{tituloDe(tatuagem)}</strong>
                      <small>{pendente ? `${pendente.ultimo_autor}: ${pendente.ultimo_texto}` : `Local: ${tatuagem.local_corpo}`}</small>
                    </span>
                    {pendente && (
                      <span className="contador" aria-label={`${pendente.nao_lidas} não lidas`}>{pendente.nao_lidas}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>

          {selecionada ? (
            <div className="painel-conversa">
              <button className="link-voltar voltar-conversas" type="button" onClick={() => aoSelecionar(null)}>
                ← Todas as conversas
              </button>
              {/* key recria a conversa ao trocar de pedido, começando sem as mensagens do anterior. */}
              <Conversa key={selecionada.id} tatuagemId={selecionada.id} usuario={usuario} titulo={tituloDe(selecionada)} aoLer={aoLer} />
            </div>
          ) : (
            <div className="estado-vazio escolha-conversa">Escolha uma conversa ao lado.</div>
          )}
        </div>
      )}
    </section>
  );
}

export default Mensagens;
