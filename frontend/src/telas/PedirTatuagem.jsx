import { useState } from "react";

import { enderecoApi } from "../api.js";
import AssistenteIA from "../componentes/AssistenteIA.jsx";

// Locais do corpo agrupados por região, para a cliente achar mais rápido.
// Os nomes continuam os mesmos de antes, então os pedidos antigos seguem iguais na agenda.
const regioesDoCorpo = [
  { regiao: "Braços e mãos", locais: ["Antebraço interno", "Antebraço externo", "Braço", "Ombro", "Mão"] },
  { regiao: "Tronco", locais: ["Peito", "Costela", "Costas"] },
  { regiao: "Cabeça e pescoço", locais: ["Nuca"] },
  { regiao: "Pernas e pés", locais: ["Coxa", "Panturrilha", "Canela", "Tornozelo", "Pé"] },
];

// Valor usado quando a cliente escolhe "Outro" e escreve o local com as próprias palavras.
const LOCAL_OUTRO = "outro";

// Permite que a cliente escolha decalques ou envie uma ideia própria ao estúdio.
function PedirTatuagem({ perfil, figuras }) {
  // useState guarda a referência escolhida, a ideia livre e os estados do envio.
  const [figuraSelecionada, definirFiguraSelecionada] = useState("");
  const [ideiaLivre, definirIdeiaLivre] = useState("");
  // Local escolhido nos botões, ou LOCAL_OUTRO; quando é "Outro", o texto fica em localOutro.
  const [localCorpo, definirLocalCorpo] = useState("");
  const [localOutro, definirLocalOutro] = useState("");
  // O local que vai para a API: o botão escolhido ou o que a cliente escreveu.
  const localFinal = localCorpo === LOCAL_OUTRO ? localOutro.trim() : localCorpo;
  // Guardado como texto porque é o que o campo devolve; vira número só no envio.
  const [tamanhoCm, definirTamanhoCm] = useState("");
  const [estado, definirEstado] = useState("pronto");
  const [mensagem, definirMensagem] = useState("");
  const [mostrarIdeiaLivre, definirMostrarIdeiaLivre] = useState(false);
  // Rascunho criado com a assistente de IA e anexado ao pedido (data URL), ou vazio.
  const [imagemIa, definirImagemIa] = useState("");
  // Atualiza o passo em destaque conforme a cliente escolhe uma referência, a região do corpo e o tamanho.
  const passoAtual = localFinal && tamanhoCm
    ? 3
    : figuraSelecionada || ideiaLivre.trim()
      ? 2
      : 1;

  // Recebe da assistente a foto de referência e o resumo da ideia, e preenche o pedido com eles.
  function usarIdeiaDaIa({ imagem, ideia }) {
    definirImagemIa(imagem);
    // Só as palavras da cliente: o pedido já é enviado como "O que vem à mente da cliente: …".
    definirIdeiaLivre(ideia);
    // Abre o campo da ideia livre para a cliente ver e ajustar o texto antes de enviar.
    definirMostrarIdeiaLivre(true);
  }

  // Alterna a escolha de uma única referência do catálogo.
  function alternarFigura(figuraId) {
    definirFiguraSelecionada((atual) => (atual === figuraId ? "" : figuraId));
  }

  // Envia as referências e a ideia própria no campo de ideia previsto na API.
  function enviarPedido(evento) {
    evento.preventDefault();
    const figuraEscolhida = figuras.find((figura) => figura.id === figuraSelecionada);
    const nomesFiguras = figuraEscolhida ? [figuraEscolhida.nome] : [];
    const partesDaIdeia = [];

    if (nomesFiguras.length > 0) {
      partesDaIdeia.push(`Referências do catálogo: ${nomesFiguras.join(", ")}`);
    }
    if (ideiaLivre.trim()) {
      partesDaIdeia.push(`O que vem à mente da cliente: ${ideiaLivre.trim()}`);
    }
    // Uma foto de referência anexada também conta como ideia, mesmo sem texto escrito.
    if (imagemIa && !ideiaLivre.trim()) {
      partesDaIdeia.push("Foto de referência anexada pela cliente");
    }

    if (partesDaIdeia.length === 0) {
      definirEstado("erro");
      definirMensagem("Selecione um decalque, anexe uma foto ou conte o que vem à sua mente.");
      return;
    }

    // Os botões de local não são campos de formulário, então o navegador não confere sozinho.
    if (!localFinal) {
      definirEstado("erro");
      definirMensagem(localCorpo === LOCAL_OUTRO ? "Escreva onde você quer tatuar." : "Escolha o local do corpo.");
      return;
    }

    definirEstado("carregando");
    definirMensagem("");

    const token = localStorage.getItem("pereiratatto-token");
    const cabecalhos = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    fetch(`${enderecoApi}/tatuagens`, {
      method: "POST",
      headers: cabecalhos,
      body: JSON.stringify({
        cliente_id: Number(perfil.id),
        ideia: partesDaIdeia.join(". "),
        local_corpo: localFinal,
        tamanho_cm: Number(tamanhoCm),
        // undefined some do JSON, então pedidos sem imagem continuam iguais.
        imagem_ia: imagemIa || undefined,
      }),
    })
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Não foi possível enviar o pedido. Confira os campos e tente novamente.");
        }
        return resposta.json();
      })
      .then(() => {
        definirEstado("pronto");
        // A cliente só precisa saber que o pedido chegou; o número é de uso interno do estúdio.
        definirMensagem("Pedido enviado com sucesso.");
        definirFiguraSelecionada("");
        definirIdeiaLivre("");
        definirLocalCorpo("");
        definirLocalOutro("");
        definirTamanhoCm("");
        definirImagemIa("");
      })
      .catch((erro) => {
        definirEstado("erro");
        definirMensagem(erro.message);
      });
  }

  return (
    <section className="painel painel-pedido">
      <section className="hero-pedido" aria-labelledby="titulo-pedido">
        <div className="hero-pedido-texto">
          <p className="sobretitulo">SUA IDEIA GANHA FORMA AQUI</p>
          <h1 id="titulo-pedido">Uma tatuagem com a sua história.</h1>
          <p className="introducao">
            Escolha uma referência visual ou conte ao estúdio o que você imagina.
          </p>
          <ol className="passos-pedido" aria-label="Etapas para pedir uma tatuagem">
            {["Inspire-se", "Local e tamanho", "Envie seu pedido"].map((passo, indice) => (
              <li className={passoAtual === indice + 1 ? "passo-pedido atual" : passoAtual > indice + 1 ? "passo-pedido concluido" : "passo-pedido"} key={passo}>
                <span>{String(indice + 1).padStart(2, "0")}</span>
                {passo}
              </li>
            ))}
          </ol>
        </div>
        <div className="hero-pedido-imagem">
          <img src="/decalques/rosa-foto.jpg" alt="Referência fotográfica de uma tatuagem de rosa" />
          <span>Referência em destaque</span>
        </div>
      </section>

      <form className="formulario" onSubmit={enviarPedido}>
        <fieldset className="campo-figuras">
          <legend>Referências de tatuagens</legend>
          <p className="ajuda-campo">Selecione uma imagem que combine com sua ideia.</p>
          <div className="grade-figuras">
            {figuras.map((figura) => (
              <button
                className={figuraSelecionada === figura.id ? "figura selecionada" : "figura"}
                type="button"
                key={figura.id}
                aria-pressed={figuraSelecionada === figura.id}
                onClick={() => alternarFigura(figura.id)}
              >
                <img className="imagem-decalque" src={figura.imagem} alt={`Imagem de referência: ${figura.nome}`} loading="lazy" />
                <span>{figura.nome}</span>
              </button>
            ))}
          </div>
          <p className="resumo-selecao">
            {!figuraSelecionada
              ? "Nenhum decalque selecionado"
              : `Selecionado: ${figuras.find((figura) => figura.id === figuraSelecionada)?.nome ?? ""}`}
          </p>
        </fieldset>

        <AssistenteIA aoUsar={usarIdeiaDaIa} />

        {/* Tudo o que a cliente preenche fica num bloco só, com título, em vez de solto no fim da página. */}
        <section className="detalhes-pedido" aria-labelledby="titulo-detalhes-pedido">
          <div className="detalhes-pedido-topo">
            <h2 id="titulo-detalhes-pedido">Detalhes do pedido</h2>
            <p>Conte sua ideia, escolha o local e o tamanho, e envie para o estúdio.</p>
          </div>

          {imagemIa && (
            <div className="rascunho-anexado">
              <img src={imagemIa} alt="Imagem de referência anexada ao pedido" />
              <p>Imagem de referência anexada. O estúdio vai recebê-la junto com o pedido.</p>
              <button className="botao-secundario" type="button" onClick={() => definirImagemIa("")}>Remover</button>
            </div>
          )}

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

          {/* Local do corpo em botões agrupados por região, com a opção "Outro" para escrever livremente. */}
          <fieldset className="seletor-local">
            <legend>Local do corpo</legend>
            <div className="regioes-local">
              {regioesDoCorpo.map(({ regiao, locais }) => (
                <div className="regiao-local" key={regiao}>
                  <p className="regiao-titulo">{regiao}</p>
                  <div className="opcoes-local">
                    {locais.map((local) => (
                      <button
                        type="button"
                        key={local}
                        className={localCorpo === local ? "opcao-local selecionada" : "opcao-local"}
                        // aria-pressed diz ao leitor de tela qual botão está escolhido.
                        aria-pressed={localCorpo === local}
                        onClick={() => definirLocalCorpo(local)}
                      >
                        {local}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <div className="regiao-local">
                <p className="regiao-titulo">Não encontrou?</p>
                <div className="opcoes-local">
                  <button
                    type="button"
                    className={localCorpo === LOCAL_OUTRO ? "opcao-local opcao-outro selecionada" : "opcao-local opcao-outro"}
                    aria-pressed={localCorpo === LOCAL_OUTRO}
                    aria-expanded={localCorpo === LOCAL_OUTRO}
                    onClick={() => definirLocalCorpo(LOCAL_OUTRO)}
                  >
                    {/* Escolhido, ganha o ✓ do estilo; o "+" só aparece enquanto ainda não foi escolhido. */}
                    {localCorpo === LOCAL_OUTRO ? "Outro" : "+ Outro"}
                  </button>
                </div>
              </div>
            </div>

            {localCorpo === LOCAL_OUTRO && (
              <label className="campo-local-outro">
                Onde você quer tatuar?
                {/* O banco guarda até 120 caracteres no local; maxLength segue esse limite. */}
                <input
                  type="text"
                  maxLength={120}
                  placeholder="Ex.: atrás da orelha, lateral do dedo, quadril…"
                  value={localOutro}
                  onChange={(evento) => definirLocalOutro(evento.target.value)}
                  required
                  autoFocus
                />
                <span className="ajuda-campo">Escreva com suas palavras; o tatuador confirma com você se precisar.</span>
              </label>
            )}
          </fieldset>

          <div className="linha-campos">
            <label className="campo-local-corpo campo-tamanho">
              Tamanho aproximado (cm)
              {/* inputMode="numeric" abre o teclado de números no celular; min e max seguem o limite da API. */}
              <span className="entrada-com-unidade">
                <input
                  type="number"
                  inputMode="numeric"
                  min="1"
                  max="100"
                  step="1"
                  placeholder="Ex.: 10"
                  value={tamanhoCm}
                  onChange={(evento) => definirTamanhoCm(evento.target.value)}
                  required
                />
                <span aria-hidden="true">cm</span>
              </span>
              <span className="ajuda-campo">Medida aproximada do lado maior do desenho.</span>
            </label>
          </div>

          <div className="detalhes-pedido-rodape">
            <button className="botao-principal" type="submit" disabled={estado === "carregando"}>
              {estado === "carregando" ? "Enviando pedido…" : "Enviar pedido"}
            </button>
          </div>
        </section>
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
