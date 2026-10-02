import { useEffect, useState } from "react";

// Os valores de etapa correspondem aos que a API já utiliza.
const etapas = ["pedida", "desenho aprovado", "em sessões", "finalizada"];

function nomeEtapa(etapa) {
  const nomes = {
    pedida: "Pedido recebido",
    "desenho aprovado": "Desenho aprovado",
    "em sessões": "Em sessões",
    sessão: "Em sessões",
    "pedido recebido": "Pedido recebido",
    retoque: "Tatuagem finalizada",
    finalizada: "Finalizada",
  };
  return nomes[etapa] || etapa;
}

// Reúne os pedidos para o tatuador consultar e abrir cada ficha.
function Agenda({ enderecoApi, aoAbrirFicha }) {
  const [etapa, definirEtapa] = useState("");
  const [busca, definirBusca] = useState("");
  const [tatuagens, definirTatuagens] = useState([]);
  const [estado, definirEstado] = useState("carregando");
  const [erro, definirErro] = useState("");
  const [pedidoDescartando, definirPedidoDescartando] = useState(null);
  const [erroAcao, definirErroAcao] = useState("");

  // Carrega os pedidos; o filtro e a busca são aplicados nesta tela.
  useEffect(() => {
    fetch(`${enderecoApi}/tatuagens`)
      .then((resposta) => {
        if (!resposta.ok) throw new Error("Não foi possível carregar a agenda.");
        return resposta.json();
      })
      .then((lista) => {
        definirTatuagens(lista);
        definirEstado("pronto");
      })
      .catch((erroBusca) => {
        definirErro(erroBusca.message);
        definirEstado("erro");
      });
  }, [enderecoApi]);

  const pedidosVisiveis = tatuagens.filter((tatuagem) => {
    const combinaEtapa = !etapa || tatuagem.etapa === etapa;
    const texto = `${tatuagem.id} ${tatuagem.ideia} ${tatuagem.local_corpo}`.toLocaleLowerCase("pt-BR");
    return combinaEtapa && texto.includes(busca.trim().toLocaleLowerCase("pt-BR"));
  });

  // Pede confirmação antes de excluir o pedido e seu histórico.
  function descartarPedido(tatuagem) {
    const confirmou = window.confirm(
      `Descartar o pedido nº ${tatuagem.id}? O histórico dele também será excluído.`,
    );
    if (!confirmou) return;

    definirPedidoDescartando(tatuagem.id);
    definirErroAcao("");
    fetch(`${enderecoApi}/tatuagens/${tatuagem.id}`, { method: "DELETE" })
      .then((resposta) => {
        if (!resposta.ok) throw new Error("Não foi possível descartar este pedido.");
        definirTatuagens((lista) => lista.filter((item) => item.id !== tatuagem.id));
        definirPedidoDescartando(null);
      })
      .catch((erroDescartar) => {
        definirErroAcao(erroDescartar.message);
        definirPedidoDescartando(null);
      });
  }

  return (
    <section className="painel painel-gestao">
      <header className="cabecalho-agenda-simples">
        <div>
          <p className="sobretitulo">ESTÚDIO PEREIRATATTO</p>
          <h1>Agenda</h1>
          <p className="introducao">Pedidos e andamento dos trabalhos.</p>
        </div>
        <span className="contador-agenda">{pedidosVisiveis.length} {pedidosVisiveis.length === 1 ? "pedido" : "pedidos"}</span>
      </header>

      <div className="filtros-agenda">
        <label className="busca-agenda">
          Buscar pedido
          <input value={busca} onChange={(evento) => definirBusca(evento.target.value)} placeholder="Número, ideia ou local" />
        </label>
        <label className="filtro-etapa">
          Filtrar por etapa
          <select value={etapa} onChange={(evento) => definirEtapa(evento.target.value)}>
            <option value="">Todas as etapas</option>
            {etapas.map((item) => <option key={item} value={item}>{nomeEtapa(item)}</option>)}
          </select>
        </label>
      </div>

      {estado === "carregando" && <p className="estado-tela">Carregando agenda…</p>}
      {estado === "erro" && <p className="aviso erro" role="alert">{erro}</p>}
      {erroAcao && <p className="aviso erro" role="alert">{erroAcao}</p>}
      {estado === "pronto" && pedidosVisiveis.length === 0 && (
        <div className="estado-vazio">{tatuagens.length === 0 ? "Ainda não há pedidos na agenda." : "Nenhum pedido encontrado com esses filtros."}</div>
      )}
      {estado === "pronto" && pedidosVisiveis.length > 0 && (
        <ul className="lista-tatuagens lista-agenda">
          {pedidosVisiveis.map((tatuagem) => (
            <li className="cartao-tatuagem cartao-agenda" key={tatuagem.id}>
              <div className="numero-agenda" aria-hidden="true">{String(tatuagem.id).padStart(2, "0")}</div>
              <div className="dados-agenda">
                <p className="identificador">PEDIDO Nº {tatuagem.id}</p>
                <h3>{tatuagem.ideia}</h3>
                <p className="local-agenda">Local: <strong>{tatuagem.local_corpo}</strong></p>
                <span className="etapa">{nomeEtapa(tatuagem.etapa)}</span>
              </div>
              <div className="acoes-agenda">
                <button className="botao-secundario" type="button" onClick={() => aoAbrirFicha(tatuagem.id)}>
                  Abrir ficha <span aria-hidden="true">→</span>
                </button>
                <button
                  className="botao-perigo"
                  type="button"
                  disabled={pedidoDescartando === tatuagem.id}
                  onClick={() => descartarPedido(tatuagem)}
                >
                  {pedidoDescartando === tatuagem.id ? "Descartando…" : "Descartar pedido"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default Agenda;
