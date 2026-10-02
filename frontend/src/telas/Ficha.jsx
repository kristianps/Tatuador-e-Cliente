import { useEffect, useState } from "react";

// Mantém os valores que a API espera e apresenta nomes corrigidos na tela.
const etapas = ["pedida", "desenho aprovado", "em sessões", "finalizada"];
const opcoesEtapa = [
  { etapa: "pedida", tipo: "pedido recebido", nome: "Pedido recebido", detalhe: "Pedido na agenda" },
  { etapa: "desenho aprovado", tipo: "desenho aprovado", nome: "Desenho aprovado", detalhe: "Arte validada" },
  { etapa: "em sessões", tipo: "sessão", nome: "Em sessões", detalhe: "Trabalho em andamento" },
  { etapa: "finalizada", tipo: "retoque", nome: "Finalizada", detalhe: "Trabalho concluído" },
];

function nomeEtapa(etapa) {
  const nomes = {
    pedida: "Pedido recebido",
    "desenho aprovado": "Desenho aprovado",
    "em sessões": "Em sessões",
    sessão: "Em sessões",
    retoque: "Tatuagem finalizada",
    finalizada: "Finalizada",
  };
  return nomes[etapa] || etapa;
}

// Permite escolher uma etapa independente para cada tatuagem.
function Ficha({ tatuagemId, enderecoApi, aoVoltar }) {
  const [tatuagem, definirTatuagem] = useState(null);
  const [passos, definirPassos] = useState([]);
  const [etapaSelecionada, definirEtapaSelecionada] = useState("");
  const [estado, definirEstado] = useState("carregando");
  const [limpandoHistorico, definirLimpandoHistorico] = useState(false);
  const [erro, definirErro] = useState("");
  const [mensagem, definirMensagem] = useState("");

  // Carrega a tatuagem e os registros já associados a ela.
  useEffect(() => {
    if (tatuagemId === null) return;

    definirTatuagem(null);
    definirEstado("carregando");
    definirErro("");
    Promise.all([
      fetch(`${enderecoApi}/tatuagens/${tatuagemId}`),
      fetch(`${enderecoApi}/tatuagens/${tatuagemId}/passos`),
    ])
      .then(async ([respostaTatuagem, respostaPassos]) => {
        if (!respostaTatuagem.ok || !respostaPassos.ok) {
          throw new Error("Não foi possível carregar esta ficha.");
        }
        return Promise.all([respostaTatuagem.json(), respostaPassos.json()]);
      })
      .then(([resultado, historico]) => {
        definirTatuagem(resultado);
        definirPassos(historico);
        definirEtapaSelecionada(resultado.etapa);
        definirEstado("pronto");
      })
      .catch((erroBusca) => {
        definirErro(erroBusca.message);
        definirEstado("erro");
      });
  }, [enderecoApi, tatuagemId]);

  const indiceEtapa = tatuagem ? etapas.indexOf(tatuagem.etapa) : -1;
  const opcaoSelecionada = opcoesEtapa.find((opcao) => opcao.etapa === etapaSelecionada);

  // A data é automática; o tatuador pode marcar diretamente a etapa deste pedido.
  function atualizarAndamento(evento) {
    evento.preventDefault();
    definirEstado("carregando");
    definirErro("");
    definirMensagem("");

    const agora = new Date();
    const hoje = new Date(agora.getTime() - agora.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 10);

    fetch(`${enderecoApi}/tatuagens/${tatuagemId}/passos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tipo: opcaoSelecionada.tipo, data: hoje, observacao: "" }),
    })
      .then((resposta) => {
        if (!resposta.ok) {
          return resposta.json().then((detalhe) => {
            throw new Error(detalhe.detail || "Não foi possível atualizar o andamento.");
          });
        }
        return resposta.json();
      })
      .then((resultado) => {
        definirTatuagem({ ...tatuagem, etapa: resultado.etapa_atualizada });
        definirEtapaSelecionada(resultado.etapa_atualizada);
        definirPassos([...passos, resultado]);
        definirMensagem(`Andamento atualizado: ${nomeEtapa(resultado.etapa_atualizada)}.`);
        definirEstado("pronto");
      })
      .catch((erroEnvio) => {
        definirErro(erroEnvio.message);
        definirEstado("erro");
      });
  }

  // Confirma e apaga somente o histórico deste pedido.
  function limparHistorico() {
    const confirmou = window.confirm(
      `Limpar o histórico do pedido nº ${tatuagem.id}? O pedido continuará na agenda.`,
    );
    if (!confirmou) return;

    definirLimpandoHistorico(true);
    definirErro("");
    fetch(`${enderecoApi}/tatuagens/${tatuagemId}/passos`, { method: "DELETE" })
      .then((resposta) => {
        if (!resposta.ok) throw new Error("Não foi possível limpar este histórico.");
        return resposta.json();
      })
      .then((resultado) => {
        definirPassos([]);
        definirMensagem(`${resultado.apagados} registros removidos do histórico.`);
        definirLimpandoHistorico(false);
      })
      .catch((erroLimpeza) => {
        definirErro(erroLimpeza.message);
        definirLimpandoHistorico(false);
      });
  }

  if (tatuagemId === null) {
    return (
      <section className="painel painel-gestao">
        <p className="sobretitulo">GESTÃO DO ESTÚDIO</p>
        <h1>Ficha de trabalho</h1>
        <p className="introducao">Escolha um pedido na agenda.</p>
        <button className="botao-principal" onClick={aoVoltar}>Voltar para a agenda</button>
      </section>
    );
  }

  if (estado === "carregando" && tatuagem === null) return <p className="estado-tela">Carregando ficha…</p>;
  if (estado === "erro" && tatuagem === null) return <p className="aviso erro" role="alert">{erro}</p>;
  if (tatuagem === null) return <p className="estado-tela">Carregando ficha…</p>;

  return (
    <section className="painel painel-gestao ficha-simples">
      <button className="link-voltar" type="button" onClick={aoVoltar}>← Voltar para a agenda</button>
      <header className="cabecalho-ficha">
        <div>
          <p className="sobretitulo">PEDIDO Nº {tatuagem.id}</p>
          <h1>Andamento</h1>
        </div>
        <span className="etapa etapa-destaque">{nomeEtapa(tatuagem.etapa)}</span>
      </header>

      <div className="resumo-ficha resumo-ficha-detalhado">
        <div><span>IDEIA</span><h2>{tatuagem.ideia}</h2></div>
        <div><span>LOCAL</span><strong>{tatuagem.local_corpo}</strong></div>
      </div>

      <form className="formulario formulario-andamento" onSubmit={atualizarAndamento}>
        <fieldset className="seletor-etapa">
          <legend>Etapa atual</legend>
          <p>Escolha em qual etapa este pedido está.</p>
          <div className="opcoes-etapa">
            {opcoesEtapa.map((opcao, indice) => (
              <button
                className={etapaSelecionada === opcao.etapa ? "opcao-etapa selecionada" : "opcao-etapa"}
                type="button"
                key={opcao.etapa}
                aria-pressed={etapaSelecionada === opcao.etapa}
                onClick={() => definirEtapaSelecionada(opcao.etapa)}
              >
                <span className="numero-etapa">0{indice + 1}</span>
                <strong>{opcao.nome}</strong>
                <small>{opcao.detalhe}</small>
              </button>
            ))}
          </div>
        </fieldset>
        <button
          className="botao-principal"
          type="submit"
          disabled={estado === "carregando" || !opcaoSelecionada || etapaSelecionada === tatuagem.etapa}
        >
          {estado === "carregando" ? "Salvando…" : etapaSelecionada === tatuagem.etapa ? "Etapa atual selecionada" : "Salvar etapa"}
        </button>
      </form>

      {estado === "erro" && <p className="aviso erro" role="alert">{erro}</p>}
      {mensagem && <p className="aviso sucesso" role="status">{mensagem}</p>}

      {passos.length > 0 && (
        <section className="historico historico-ficha">
          <div className="cabecalho-historico-simples">
            <h2>Atualizações</h2>
            <button className="botao-perigo" type="button" disabled={limpandoHistorico} onClick={limparHistorico}>
              {limpandoHistorico ? "Limpando…" : "Limpar histórico"}
            </button>
          </div>
          <ul className="atualizacoes-simples">
            {passos.map((passo) => (
              <li key={passo.id}>{nomeEtapa(passo.etapa_atualizada || passo.tipo)} · {new Date(`${passo.data}T12:00:00`).toLocaleDateString("pt-BR")}</li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}

export default Ficha;
