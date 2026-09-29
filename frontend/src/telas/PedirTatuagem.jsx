import { useState } from "react";

// Permite que a cliente escolha decalques ou envie uma ideia própria ao estúdio.
function PedirTatuagem({ perfil, enderecoApi, figuras }) {
  // useState guarda as referências escolhidas, a ideia livre e os estados do envio.
  const [figurasSelecionadas, definirFigurasSelecionadas] = useState([]);
  const [ideiaLivre, definirIdeiaLivre] = useState("");
  const [localCorpo, definirLocalCorpo] = useState("");
  const [tamanho, definirTamanho] = useState("");
  const [estado, definirEstado] = useState("pronto");
  const [mensagem, definirMensagem] = useState("");
  const [mostrarIdeiaLivre, definirMostrarIdeiaLivre] = useState(false);

  // Alterna a escolha de um decalque sem impedir que a cliente selecione outros.
  function alternarFigura(figuraId) {
    if (figurasSelecionadas.includes(figuraId)) {
      definirFigurasSelecionadas(
        figurasSelecionadas.filter((id) => id !== figuraId),
      );
      return;
    }

    definirFigurasSelecionadas([...figurasSelecionadas, figuraId]);
  }

  // Envia as referências e a ideia própria no campo de ideia previsto na API.
  function enviarPedido(evento) {
    evento.preventDefault();
    const nomesFiguras = figuras
      .filter((figura) => figurasSelecionadas.includes(figura.id))
      .map((figura) => figura.nome);
    const partesDaIdeia = [];

    if (nomesFiguras.length > 0) {
      partesDaIdeia.push(`Referências do catálogo: ${nomesFiguras.join(", ")}`);
    }
    if (ideiaLivre.trim()) {
      partesDaIdeia.push(`O que vem à mente da cliente: ${ideiaLivre.trim()}`);
    }

    if (partesDaIdeia.length === 0) {
      definirEstado("erro");
      definirMensagem("Selecione um decalque ou conte o que vem à sua mente.");
      return;
    }

    definirEstado("carregando");
    definirMensagem("");

    // fetch envia o POST em JSON; o then trata resposta.ok e o catch mostra falhas.
    fetch(`${enderecoApi}/tatuagens`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cliente_id: Number(perfil.id),
        ideia: partesDaIdeia.join(". "),
        local_corpo: localCorpo,
        tamanho,
      }),
    })
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Não foi possível enviar o pedido. Confira os campos e tente novamente.");
        }
        return resposta.json();
      })
      .then((tatuagem) => {
        definirEstado("pronto");
        definirMensagem(`Pedido ${tatuagem.id} enviado. Etapa atual: ${tatuagem.etapa}.`);
        definirFigurasSelecionadas([]);
        definirIdeiaLivre("");
        definirLocalCorpo("");
        definirTamanho("");
      })
      .catch((erro) => {
        definirEstado("erro");
        definirMensagem(erro.message);
      });
  }

  return (
    <section className="painel">
      <p className="sobretitulo">PARA COMEÇAR</p>
      <h1>Pedir tatuagem</h1>
      <p className="introducao">
        Escolha referências visuais ou conte ao estúdio o que você imagina.
      </p>

      <form className="formulario" onSubmit={enviarPedido}>
        <fieldset className="campo-figuras">
          <legend>Decalques do catálogo</legend>
          <p className="ajuda-campo">Selecione ou desmarque as figuras que combinam com sua ideia.</p>
          <div className="grade-figuras">
            {figuras.map((figura) => (
              <button
                className={figurasSelecionadas.includes(figura.id) ? "figura selecionada" : "figura"}
                type="button"
                key={figura.id}
                aria-pressed={figurasSelecionadas.includes(figura.id)}
                onClick={() => alternarFigura(figura.id)}
              >
                <img className="imagem-decalque" src={figura.imagem} alt={`Decalque de ${figura.nome}`} />
                <span>{figura.nome}</span>
              </button>
            ))}
          </div>
          <p className="resumo-selecao">
            {figurasSelecionadas.length === 0
              ? "Nenhum decalque selecionado"
              : `Selecionados: ${figuras
                  .filter((figura) => figurasSelecionadas.includes(figura.id))
                  .map((figura) => figura.nome)
                  .join(", ")}`}
          </p>
        </fieldset>

        <section className="ideia-personalizada">
          <button
            className="botao-secundario"
            type="button"
            aria-expanded={mostrarIdeiaLivre}
            onClick={() => definirMostrarIdeiaLivre(!mostrarIdeiaLivre)}
          >
            {mostrarIdeiaLivre ? "Fechar ideia livre" : "Não encontrou? Conte o que vem à mente"}
          </button>

          {mostrarIdeiaLivre && (
            <label className="campo-ideia-livre">
              O que vem à sua mente?
              <textarea
                value={ideiaLivre}
                onChange={(evento) => definirIdeiaLivre(evento.target.value)}
                placeholder="Conte sua ideia com suas palavras. Não precisa escolher uma imagem."
              />
              <span className="ajuda-campo">
                O estúdio recebe sua ideia junto com o pedido e pode usá-la como referência para novas opções do catálogo.
              </span>
            </label>
          )}
        </section>

        <div className="linha-campos">
          <label>
            Local do corpo
            <input
              value={localCorpo}
              onChange={(evento) => definirLocalCorpo(evento.target.value)}
              placeholder="Ex.: antebraço"
              required
            />
          </label>
          <label>
            Tamanho
            <input
              value={tamanho}
              onChange={(evento) => definirTamanho(evento.target.value)}
              placeholder="Ex.: 15 cm"
              required
            />
          </label>
        </div>

        <button className="botao-principal" type="submit" disabled={estado === "carregando"}>
          {estado === "carregando" ? "Enviando pedido…" : "Enviar pedido"}
        </button>
      </form>

      {mensagem && (
        <p className={estado === "erro" ? "aviso erro" : "aviso sucesso"} role="status">
          {mensagem}
        </p>
      )}
    </section>
  );
}

export default PedirTatuagem;
