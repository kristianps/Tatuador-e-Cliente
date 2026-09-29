import { useState } from "react";

import Agenda from "./telas/Agenda.jsx";
import Ficha from "./telas/Ficha.jsx";
import MinhasTatuagens from "./telas/MinhasTatuagens.jsx";
import PedirTatuagem from "./telas/PedirTatuagem.jsx";

const enderecoApi = "http://127.0.0.1:8000";

// Reúne quinze decalques ilustrados para a cliente escolher no pedido.
const figurasIniciais = [
  { id: "rosa", nome: "Rosa", imagem: "/decalques/rosa.svg" },
  { id: "dragao", nome: "Dragão", imagem: "/decalques/dragao.svg" },
  { id: "borboleta", nome: "Borboleta", imagem: "/decalques/borboleta.svg" },
  { id: "caveira", nome: "Caveira", imagem: "/decalques/caveira.svg" },
  { id: "serpente", nome: "Serpente", imagem: "/decalques/serpente.svg" },
  { id: "lua", nome: "Lua", imagem: "/decalques/lua.svg" },
  { id: "sol", nome: "Sol", imagem: "/decalques/sol.svg" },
  { id: "lobo", nome: "Lobo", imagem: "/decalques/lobo.svg" },
  { id: "aguia", nome: "Águia", imagem: "/decalques/aguia.svg" },
  { id: "coracao", nome: "Coração", imagem: "/decalques/coracao.svg" },
  { id: "lotus", nome: "Flor de lótus", imagem: "/decalques/lotus.svg" },
  { id: "adaga", nome: "Adaga", imagem: "/decalques/adaga.svg" },
  { id: "estrela", nome: "Estrela náutica", imagem: "/decalques/estrela.svg" },
  { id: "montanhas", nome: "Montanhas", imagem: "/decalques/montanhas.svg" },
  { id: "andorinha", nome: "Andorinha", imagem: "/decalques/andorinha.svg" },
];

// Apresenta a escolha de perfil e as duas telas correspondentes a cada pessoa.
function Aplicacao() {
  // useState guarda escolhas que mudam e faz a tela ser atualizada quando elas mudam.
  const [perfilId, definirPerfilId] = useState("1");
  const [telaAtual, definirTelaAtual] = useState("pedir");
  const [tatuagemId, definirTatuagemId] = useState(null);

  const perfis = [
    { id: "1", nome: "Bruna — cliente", tipo: "cliente" },
    { id: "2", nome: "Vitor — tatuador", tipo: "tatuador" },
  ];
  const perfil = perfis.find((item) => item.id === perfilId);

  // Troca o perfil e abre a primeira tela adequada a cada tipo de pessoa.
  function trocarPerfil(evento) {
    const novoPerfilId = evento.target.value;
    const novoPerfil = perfis.find((item) => item.id === novoPerfilId);

    definirPerfilId(novoPerfilId);
    definirTatuagemId(null);
    definirTelaAtual(novoPerfil.tipo === "cliente" ? "pedir" : "agenda");
  }

  // Abre a ficha selecionada a partir de uma tatuagem da agenda.
  function abrirFicha(id) {
    definirTatuagemId(id);
    definirTelaAtual("ficha");
  }

  // Volta para a agenda sem perder o perfil de gestão escolhido.
  function voltarParaAgenda() {
    definirTelaAtual("agenda");
  }

  // Mostra a navegação e o componente da tela escolhida para o perfil.
  function mostrarTela() {
    if (perfil.tipo === "cliente" && telaAtual === "pedir") {
      return (
        <PedirTatuagem
          perfil={perfil}
          enderecoApi={enderecoApi}
          figuras={figurasIniciais}
        />
      );
    }

    if (perfil.tipo === "cliente") {
      return <MinhasTatuagens perfil={perfil} enderecoApi={enderecoApi} />;
    }

    if (telaAtual === "ficha") {
      return (
        <Ficha
          tatuagemId={tatuagemId}
          enderecoApi={enderecoApi}
          aoVoltar={voltarParaAgenda}
        />
      );
    }

    return (
      <Agenda enderecoApi={enderecoApi} aoAbrirFicha={abrirFicha} />
    );
  }

  return (
    <div className="aplicacao">
      <header className="cabecalho">
        <a className="marca" href="#inicio" onClick={() => definirTelaAtual(perfil.tipo === "cliente" ? "pedir" : "agenda")}>
          Pereira<span>Tatto</span>
        </a>
        <p className="assinatura">ESTÚDIO DE TATUAGEM</p>

        <label className="seletor-perfil">
          <span>Perfil</span>
          <select value={perfilId} onChange={trocarPerfil}>
            {perfis.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nome}
              </option>
            ))}
          </select>
        </label>
      </header>

      <nav className="navegacao" aria-label="Navegação principal">
        {perfil.tipo === "cliente" ? (
          <>
            <button
              className={telaAtual === "pedir" ? "aba ativa" : "aba"}
              onClick={() => definirTelaAtual("pedir")}
            >
              Pedir tatuagem
            </button>
            <button
              className={telaAtual === "minhas" ? "aba ativa" : "aba"}
              onClick={() => definirTelaAtual("minhas")}
            >
              Minhas tatuagens
            </button>
          </>
        ) : (
          <>
            <button
              className={telaAtual === "agenda" ? "aba ativa" : "aba"}
              onClick={() => definirTelaAtual("agenda")}
            >
              A agenda
            </button>
            <button
              className={telaAtual === "ficha" ? "aba ativa" : "aba"}
              onClick={() => definirTelaAtual("ficha")}
            >
              A ficha
            </button>
          </>
        )}
      </nav>

      <main className="conteudo" id="inicio">
        {mostrarTela()}
      </main>

      <footer className="rodape">PereiraTatto · cuidado em cada etapa</footer>
    </div>
  );
}

export default Aplicacao;
