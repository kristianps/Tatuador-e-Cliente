import { useEffect, useState } from "react";

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

  // useEffect repete a consulta quando o perfil muda; fetch mantém os estados de tela claros.
  useEffect(() => {
    definirEstado("carregando");
    fetch(`${enderecoApi}/tatuagens?cliente_id=${perfil.id}`)
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Não foi possível carregar suas tatuagens.");
        }
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
  }, [enderecoApi, perfil.id]);

  // Busca os passos de uma tatuagem para exibir o histórico dentro desta tela.
  function abrirHistorico(tatuagem) {
    definirTatuagemAberta(tatuagem);
    definirPassos([]);
    definirEstadoHistorico("carregando");
    definirErroHistorico("");

    fetch(`${enderecoApi}/tatuagens/${tatuagem.id}/passos?cliente_id=${perfil.id}`)
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
                <p>{tatuagem.local_corpo} · {tatuagem.tamanho}</p>
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
