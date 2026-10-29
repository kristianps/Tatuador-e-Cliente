import { useEffect, useState } from "react";

import { enderecoApi } from "./api.js";
import Agenda from "./telas/Agenda.jsx";
import Ficha from "./telas/Ficha.jsx";
import MinhasTatuagens from "./telas/MinhasTatuagens.jsx";
import PedirTatuagem from "./telas/PedirTatuagem.jsx";

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

function Aplicacao() {
  const [email, definirEmail] = useState("bruna@pereiratatto.com");
  const [senha, definirSenha] = useState("bruna123");
  const [usuario, definirUsuario] = useState(null);
  const [estadoLogin, definirEstadoLogin] = useState("pronto");
  const [erroLogin, definirErroLogin] = useState("");
  const [telaAtual, definirTelaAtual] = useState("pedir");
  const [tatuagemId, definirTatuagemId] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("pereiratatto-token");
    const usuarioSalvo = localStorage.getItem("pereiratatto-usuario");

    if (token && usuarioSalvo) {
      try {
        definirUsuario(JSON.parse(usuarioSalvo));
      } catch {
        localStorage.removeItem("pereiratatto-token");
        localStorage.removeItem("pereiratatto-usuario");
      }
    }
  }, []);

  function trocarPerfil(novoPerfilId) {
    const perfil = novoPerfilId === "cliente" ? "cliente" : "tatuador";
    const dados = perfil === "cliente"
      ? { id: 1, nome: "Bruna", perfil: "cliente" }
      : { id: 2, nome: "Vitor", perfil: "tatuador" };

    definirUsuario(dados);
    definirTatuagemId(null);
    definirTelaAtual(perfil === "cliente" ? "pedir" : "agenda");
    localStorage.setItem("pereiratatto-usuario", JSON.stringify(dados));
  }

  function fazerLogin(evento) {
    evento.preventDefault();
    definirEstadoLogin("carregando");
    definirErroLogin("");

    fetch(`${enderecoApi}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    })
      .then((resposta) => {
        if (!resposta.ok) {
          return resposta.json().then((detalhe) => {
            throw new Error(detalhe.detail || "Credenciais inválidas.");
          });
        }
        return resposta.json();
      })
      .then((resultado) => {
        localStorage.setItem("pereiratatto-token", resultado.access_token);
        localStorage.setItem("pereiratatto-usuario", JSON.stringify(resultado.usuario));
        definirUsuario(resultado.usuario);
        definirEstadoLogin("pronto");
        definirTelaAtual(resultado.usuario.perfil === "cliente" ? "pedir" : "agenda");
      })
      .catch((erro) => {
        definirErroLogin(erro.message);
        definirEstadoLogin("erro");
      });
  }

  function realizarLogout() {
    localStorage.removeItem("pereiratatto-token");
    localStorage.removeItem("pereiratatto-usuario");
    definirUsuario(null);
    definirTelaAtual("pedir");
    definirTatuagemId(null);
  }

  function abrirFicha(id) {
    definirTatuagemId(id);
    definirTelaAtual("ficha");
  }

  function voltarParaAgenda() {
    definirTelaAtual("agenda");
  }

  function mostrarTela() {
    if (!usuario) {
      return (
        <section className="painel">
          <p className="sobretitulo">ACESSO AO SISTEMA</p>
          <h1>Entrar no PereiraTatto</h1>
          <form className="formulario" onSubmit={fazerLogin}>
            <label className="campo-local-corpo">
              E-mail
              <input type="email" value={email} onChange={(evento) => definirEmail(evento.target.value)} required />
            </label>
            <label className="campo-local-corpo">
              Senha
              <input type="password" value={senha} onChange={(evento) => definirSenha(evento.target.value)} required />
            </label>
            <button className="botao-principal" type="submit" disabled={estadoLogin === "carregando"}>
              {estadoLogin === "carregando" ? "Entrando…" : "Entrar"}
            </button>
          </form>
          {erroLogin && <p className="aviso erro" role="alert">{erroLogin}</p>}
          <p className="introducao">Demo: Bruna — bruna@pereiratatto.com / bruna123 ou Vitor — vitor@pereiratatto.com / vitor123</p>
        </section>
      );
    }

    if (usuario.perfil === "cliente" && telaAtual === "pedir") {
      return <PedirTatuagem perfil={usuario} enderecoApi={enderecoApi} figuras={figurasIniciais} />;
    }

    if (usuario.perfil === "cliente") {
      return <MinhasTatuagens perfil={usuario} enderecoApi={enderecoApi} />;
    }

    if (telaAtual === "ficha") {
      return <Ficha tatuagemId={tatuagemId} enderecoApi={enderecoApi} aoVoltar={voltarParaAgenda} />;
    }

    return <Agenda enderecoApi={enderecoApi} aoAbrirFicha={abrirFicha} />;
  }

  return (
    <div className="aplicacao">
      <header className="cabecalho">
        <a className="marca" href="#inicio" onClick={() => definirTelaAtual(usuario?.perfil === "cliente" ? "pedir" : "agenda")}>
          Pereira<span>Tatto</span>
        </a>
        <p className="assinatura">ESTÚDIO DE TATUAGEM</p>

        {usuario && (
          <div className="seletor-perfil" role="group" aria-label="Sessão do usuário">
            <span className="rotulo-perfil">Sessão ativa</span>
            <div className="opcoes-perfil">
              <button className="opcao-perfil ativa" type="button">
                <span className="icone-perfil" aria-hidden="true">{usuario.perfil === "cliente" ? "B" : "V"}</span>
                <span><strong>{usuario.nome}</strong><small>{usuario.perfil === "cliente" ? "Cliente" : "Tatuador"}</small></span>
              </button>
            </div>
            <button className="botao-secundario" type="button" onClick={realizarLogout}>Sair</button>
          </div>
        )}
      </header>

      {usuario && (
        <nav className="navegacao" aria-label="Navegação principal">
          {usuario.perfil === "cliente" ? (
            <>
              <button className={telaAtual === "pedir" ? "aba ativa" : "aba"} onClick={() => definirTelaAtual("pedir")}>Pedir tatuagem</button>
              <button className={telaAtual === "minhas" ? "aba ativa" : "aba"} onClick={() => definirTelaAtual("minhas")}>Minhas tatuagens</button>
            </>
          ) : (
            <>
              <button className={telaAtual === "agenda" ? "aba ativa" : "aba"} onClick={() => definirTelaAtual("agenda")}>A agenda</button>
              <button className={telaAtual === "ficha" ? "aba ativa" : "aba"} onClick={() => definirTelaAtual("ficha")}>A ficha</button>
            </>
          )}
        </nav>
      )}

      <main className="conteudo" id="inicio">
        {mostrarTela()}
      </main>

      <footer className="rodape">PereiraTatto · cuidado em cada etapa</footer>
    </div>
  );
}

export default Aplicacao;
