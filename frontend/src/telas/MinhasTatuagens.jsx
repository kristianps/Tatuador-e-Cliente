import { useEffect, useState } from "react";

const chaveCelebracoes = (clienteId) => `pereiratatto-finalizadas-${clienteId}`;

// Mostra os pedidos da cliente e o histórico da tatuagem que ela abrir.
function MinhasTatuagens({ perfil, enderecoApi }) {
  // useState guarda a lista, o histórico selecionado e os estados de carregamento.
  const [tatuagens, definirTatuagens] = useState([]);
  const [estado, definirEstado] = useState("carregando");
  const [erro, definirErro] = useState("");
  const [tatuagemAberta, definirTatuagemAberta] = useState(null);
  const [passos, definirPassos] = useState([]);
  const [estadoHistorico, definirEstadoHistorico] = useState("pronto");
  const [erroHistorico, definirErroHistorico] = useState("");
  const [celebracao, definirCelebracao] = useState(null);

  // Atualiza a lista periodicamente e celebra cada pedido finalizado uma única vez.
  useEffect(() => {
    definirEstado("carregando");
    let ativo = true;
    let consultando = false;
    const IDsVistosNaSessao = new Set();

    function consultarPedidos() {
      if (consultando) return;
      consultando = true;
      const token = localStorage.getItem("pereiratatto-token");

      fetch(`${enderecoApi}/tatuagens?cliente_id=${perfil.id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((resposta) => {
          if (!resposta.ok) throw new Error("Não foi possível carregar suas tatuagens.");
          return resposta.json();
        })
        .then((lista) => {
          if (!ativo) return;

          definirTatuagens(lista);
          definirEstado("pronto");
          definirErro("");

          const chave = chaveCelebracoes(perfil.id);
          let IDsCelebrados = [];
          try {
            const armazenados = JSON.parse(localStorage.getItem(chave) || "[]");
            IDsCelebrados = Array.isArray(armazenados) ? armazenados : [];
          } catch {
            IDsCelebrados = [];
          }

          const finalizados = lista.filter((tatuagem) => tatuagem.etapa === "finalizada");
          const identificador = (tatuagem) => String(tatuagem.id);
          const jáCelebrados = new Set([...IDsCelebrados, ...IDsVistosNaSessao]);
          const novos = finalizados.filter((tatuagem) => !jáCelebrados.has(identificador(tatuagem)));

          if (novos.length > 0) {
            definirCelebracao({ chave: Date.now(), quantidade: novos.length });
            novos.forEach((tatuagem) => IDsVistosNaSessao.add(identificador(tatuagem)));
            const IDsAtualizados = [...new Set([
              ...IDsCelebrados,
              ...finalizados.map(identificador),
            ])];
            try {
              localStorage.setItem(chave, JSON.stringify(IDsAtualizados));
            } catch {
              // A comemoração continua disponível mesmo se o navegador bloquear o armazenamento local.
            }
          }
        })
        .catch((erroBusca) => {
          if (!ativo) return;
          definirErro(erroBusca.message);
          definirEstado("erro");
        })
        .finally(() => {
          consultando = false;
        });
    }

    consultarPedidos();
    const intervalo = window.setInterval(consultarPedidos, 5000);

    return () => {
      ativo = false;
      window.clearInterval(intervalo);
    };
  }, [enderecoApi, perfil.id]);

  // Busca os passos de uma tatuagem para exibir o histórico dentro desta tela.
  function abrirHistorico(tatuagem) {
    definirTatuagemAberta(tatuagem);
    definirPassos([]);
    definirEstadoHistorico("carregando");
    definirErroHistorico("");

    const token = localStorage.getItem("pereiratatto-token");
    fetch(`${enderecoApi}/tatuagens/${tatuagem.id}/passos?cliente_id=${perfil.id}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Não foi possível carregar o histórico.");
        }
        return resposta.json();
      })
      .then((lista) => {
        definirPassos(lista);
        definirEstadoHistorico("pronto");
      })
      .catch((erroBusca) => {
        definirErroHistorico(erroBusca.message);
        definirEstadoHistorico("erro");
      });
  }

  // Fecha o histórico selecionado sem sair da lista da cliente.
  function fecharHistorico() {
    definirTatuagemAberta(null);
    definirPassos([]);
    definirEstadoHistorico("pronto");
  }

  if (estado === "carregando") {
    return <p className="estado-tela">Carregando suas tatuagens…</p>;
  }

  if (estado === "erro") {
    return <p className="aviso erro" role="alert">{erro}</p>;
  }

  return (
    <section className="painel">
      {celebracao && (
        <section
          key={celebracao.chave}
          className="celebracao-finalizacao"
          role="status"
          aria-live="polite"
          onAnimationEnd={(evento) => {
            if (evento.target === evento.currentTarget) definirCelebracao(null);
          }}
        >
          <div className="confetes" aria-hidden="true">
            {Array.from({ length: 24 }, (_, indice) => (
              <span
                className={`confete confete-${indice % 4}`}
                key={indice}
                style={{ left: `${(indice * 43) % 100}%`, animationDelay: `${(indice % 8) * 0.09}s` }}
              />
            ))}
          </div>
          <button className="fechar-celebracao" type="button" onClick={() => definirCelebracao(null)} aria-label="Fechar comemoração">×</button>
          <p className="sobretitulo">ETAPA CONCLUÍDA</p>
          <h2>{celebracao.quantidade === 1 ? "Sua tatuagem está finalizada!" : `${celebracao.quantidade} tatuagens finalizadas!`}</h2>
          <p>Obrigado por confiar sua ideia à PereiraTatto.</p>
        </section>
      )}
      <p className="sobretitulo">ACOMPANHAMENTO</p>
      <h1>Minhas tatuagens</h1>
      <p className="introducao">Veja a etapa atual e abra uma tatuagem para consultar o histórico.</p>

      {tatuagens.length === 0 ? (
        <div className="estado-vazio">Você ainda não tem tatuagens cadastradas.</div>
      ) : (
        <ul className="lista-tatuagens">
          {/* map transforma cada item da lista em um cartão da tela. */}
          {tatuagens.map((tatuagem) => (
            <li className="cartao-tatuagem" key={tatuagem.id}>
              <div>
                <h2>{tatuagem.ideia}</h2>
                <p>{tatuagem.local_corpo}</p>
                <span className="etapa">{tatuagem.etapa}</span>
              </div>
              <button className="botao-secundario" onClick={() => abrirHistorico(tatuagem)}>
                Ver histórico
              </button>
            </li>
          ))}
        </ul>
      )}

      {tatuagemAberta && (
        <section className="historico">
          <div className="titulo-historico">
            <div>
              <p className="sobretitulo">HISTÓRICO</p>
              <h2>{tatuagemAberta.ideia}</h2>
            </div>
            <button className="botao-secundario" onClick={fecharHistorico}>Fechar</button>
          </div>

          {estadoHistorico === "carregando" && <p>Carregando histórico…</p>}
          {estadoHistorico === "erro" && <p className="aviso erro">{erroHistorico}</p>}
          {estadoHistorico === "pronto" && passos.length === 0 && (
            <p className="estado-vazio">Ainda não há passos registrados.</p>
          )}
          {estadoHistorico === "pronto" && passos.length > 0 && (
            <ol className="lista-passos">
              {passos.map((passo) => (
                <li key={passo.id}>
                  <strong>{passo.tipo}</strong>
                  <time dateTime={passo.data}>{passo.data}</time>
                  {passo.observacao && <p>{passo.observacao}</p>}
                </li>
              ))}
            </ol>
          )}
        </section>
      )}
    </section>
  );
}

export default MinhasTatuagens;
