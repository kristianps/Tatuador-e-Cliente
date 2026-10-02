import { useState } from "react";

import Agenda from "./telas/Agenda.jsx";
import Ficha from "./telas/Ficha.jsx";
import MinhasTatuagens from "./telas/MinhasTatuagens.jsx";
import PedirTatuagem from "./telas/PedirTatuagem.jsx";

const enderecoApi = "http://127.0.0.1:8000";

// Mantém somente as onze referências do catálogo que já têm imagem de tatuagem ou flash.
const figurasIniciais = [
  { id: "rosa", nome: "Rosa", imagem: "/decalques/rosa-foto.jpg" },
  { id: "dragao", nome: "Dragão", imagem: "/decalques/dragao.jpg" },
  { id: "borboleta", nome: "Borboleta", imagem: "/decalques/borboleta_a.jpg" },
  { id: "caveira", nome: "Caveira", imagem: "/decalques/caveira-foto.jpg" },
  { id: "serpente", nome: "Serpente", imagem: "/decalques/serpente-foto.jpg" },
  { id: "lua", nome: "Lua e sol", imagem: "/decalques/lua-foto.jpg" },
  { id: "lobo", nome: "Lobo", imagem: "/decalques/lobo-foto.jpg" },
  { id: "aguia", nome: "Águia", imagem: "/decalques/aguia-foto.jpg" },
  { id: "coracao", nome: "Coração e âncora", imagem: "/decalques/ancora.jpg" },
  { id: "adaga", nome: "Adaga", imagem: "/decalques/adaga-foto.jpg" },
  { id: "naval", nome: "Composição naval", imagem: "/decalques/naval_recorte.jpg" },
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
  function trocarPerfil(novoPerfilId) {
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

        <div className="seletor-perfil" role="group" aria-label="Escolha como entrar">
          <span className="rotulo-perfil">Acessar como</span>
          <div className="opcoes-perfil">
            {perfis.map((item) => (
              <button
                className={item.id === perfilId ? "opcao-perfil ativa" : "opcao-perfil"}
                type="button"
                key={item.id}
                aria-pressed={item.id === perfilId}
                onClick={() => trocarPerfil(item.id)}
              >
                <span className="icone-perfil" aria-hidden="true">{item.tipo === "cliente" ? "B" : "V"}</span>
                <span><strong>{item.tipo === "cliente" ? "Bruna" : "Vitor"}</strong><small>{item.tipo === "cliente" ? "Cliente" : "Tatuador"}</small></span>
              </button>
            ))}
          </div>
        </div>
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
