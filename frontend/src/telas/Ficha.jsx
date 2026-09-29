import { useEffect, useState } from "react";

// Mostra uma tatuagem e permite registrar um passo na sequência da cartilha.
function Ficha({ tatuagemId, enderecoApi, aoVoltar }) {
  // useState guarda a tatuagem, o formulário e o estado de leitura ou envio.
  const [tatuagem, definirTatuagem] = useState(null);
  const [tipo, definirTipo] = useState("desenho aprovado");
  const [data, definirData] = useState("");
  const [observacao, definirObservacao] = useState("");
  const [estado, definirEstado] = useState("carregando");
  const [erro, definirErro] = useState("");
  const [mensagem, definirMensagem] = useState("");

  // useEffect busca de novo se outra tatuagem for escolhida na agenda.
  useEffect(() => {
    if (tatuagemId === null) {
      definirEstado("pronto");
      return;
    }

    definirEstado("carregando");
    fetch(`${enderecoApi}/tatuagens/${tatuagemId}`)
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Não foi possível carregar esta tatuagem.");
        }
        return resposta.json();
      })
      .then((resultado) => {
        definirTatuagem(resultado);
        definirEstado("pronto");
      })
      .catch((erroBusca) => {
        definirErro(erroBusca.message);
        definirEstado("erro");
      });
  }, [enderecoApi, tatuagemId]);

  // Envia o passo escolhido e apresenta a etapa devolvida pelo serviço.
  function enviarPasso(evento) {
    evento.preventDefault();
    definirEstado("carregando");
    definirErro("");
    definirMensagem("");

    // fetch envia o POST em JSON; o then verifica a resposta e o catch apresenta o erro.
    fetch(`${enderecoApi}/tatuagens/${tatuagemId}/passos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tipo, data, observacao }),
    })
      .then((resposta) => {
        if (!resposta.ok) {
          return resposta.json().then((detalhe) => {
            throw new Error(detalhe.detail || "Não foi possível registrar este passo.");
          });
        }
        return resposta.json();
      })
      .then((resultado) => {
        definirTatuagem({ ...tatuagem, etapa: resultado.etapa_atualizada });
        definirMensagem(`Passo registrado. Nova etapa: ${resultado.etapa_atualizada}.`);
        definirData("");
        definirObservacao("");
        definirEstado("pronto");
      })
      .catch((erroEnvio) => {
        definirErro(erroEnvio.message);
        definirEstado("erro");
      });
  }

  if (estado === "carregando" && tatuagem === null && tatuagemId !== null) {
    return <p className="estado-tela">Carregando ficha…</p>;
  }

  if (tatuagemId === null) {
    return (
      <section className="painel">
        <p className="sobretitulo">GESTÃO DO ESTÚDIO</p>
        <h1>A ficha</h1>
        <p className="introducao">Escolha uma tatuagem na agenda para abrir a ficha.</p>
        <button className="botao-principal" onClick={aoVoltar}>Ir para a agenda</button>
      </section>
    );
  }

  if (estado === "erro" && tatuagem === null) {
    return <p className="aviso erro" role="alert">{erro}</p>;
  }

  if (tatuagem === null) {
    return <p className="estado-tela">Carregando ficha…</p>;
  }

  return (
    <section className="painel">
      <p className="sobretitulo">TATUAGEM Nº {tatuagem.id}</p>
      <h1>A ficha</h1>
      <div className="resumo-ficha">
        <h2>{tatuagem.ideia}</h2>
        <p>{tatuagem.local_corpo} · {tatuagem.tamanho}</p>
        <span className="etapa">Etapa: {tatuagem.etapa}</span>
      </div>

      <h2 className="titulo-secao">Registrar um passo</h2>
      <form className="formulario" onSubmit={enviarPasso}>
        <label>
          Tipo do passo
          <select value={tipo} onChange={(evento) => definirTipo(evento.target.value)}>
            <option value="desenho aprovado">Desenho aprovado</option>
            <option value="sessão">Sessão</option>
            <option value="retoque">Retoque</option>
          </select>
        </label>
        <label>
          Data
          <input type="date" value={data} onChange={(evento) => definirData(evento.target.value)} required />
        </label>
        <label>
          Observação
          <textarea
            value={observacao}
            onChange={(evento) => definirObservacao(evento.target.value)}
            placeholder="Anote o que foi feito neste passo"
          />
        </label>
        <button className="botao-principal" type="submit" disabled={estado === "carregando"}>
          {estado === "carregando" ? "Salvando passo…" : "Registrar passo"}
        </button>
      </form>

      {estado === "erro" && <p className="aviso erro" role="alert">{erro}</p>}
      {mensagem && <p className="aviso sucesso" role="status">{mensagem}</p>}
    </section>
  );
}

export default Ficha;
