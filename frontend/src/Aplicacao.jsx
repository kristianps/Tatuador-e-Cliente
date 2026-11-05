import { useEffect, useRef, useState } from "react";

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
  const [nome, definirNome] = useState("");
  const [email, definirEmail] = useState("");
  const [senha, definirSenha] = useState("");
  const [emailCadastro, definirEmailCadastro] = useState("");
  const [senhaCadastro, definirSenhaCadastro] = useState("");
  const [confirmacaoSenha, definirConfirmacaoSenha] = useState("");
  const [usuario, definirUsuario] = useState(null);
  const [estadoLogin, definirEstadoLogin] = useState("pronto");
  const [estadoCadastro, definirEstadoCadastro] = useState("pronto");
  const [erroLogin, definirErroLogin] = useState("");
  const [erroCadastro, definirErroCadastro] = useState("");
  const [mensagemCadastro, definirMensagemCadastro] = useState("");
  const [abaAtiva, definirAbaAtiva] = useState("login");
  const [telaAtual, definirTelaAtual] = useState("pedir");
  const [tatuagemId, definirTatuagemId] = useState(null);
  const cabecalhoRef = useRef(null);

  // A barra acompanha a rolagem: some aos poucos ao descer e volta na mesma medida ao subir.
  useEffect(() => {
    const cabecalho = cabecalhoRef.current;
    let ultimaPosicao = Math.max(window.scrollY, 0);
    let deslocamento = 0;

    function posicionar(novoDeslocamento) {
      deslocamento = novoDeslocamento;
      cabecalho.style.transform = `translateY(${-deslocamento}px)`;
      cabecalho.classList.toggle("recolhido", deslocamento > 0 && deslocamento >= cabecalho.offsetHeight);
    }

    function aoRolar() {
      const posicao = Math.max(window.scrollY, 0);
      const novoDeslocamento = deslocamento + posicao - ultimaPosicao;
      ultimaPosicao = posicao;
      posicionar(Math.min(Math.max(novoDeslocamento, 0), cabecalho.offsetHeight));
    }

    // Quem navega pelo teclado precisa enxergar o item da barra que recebeu o foco.
    function aoFocar() {
      posicionar(0);
    }

    window.addEventListener("scroll", aoRolar, { passive: true });
    cabecalho.addEventListener("focusin", aoFocar);

    return () => {
      window.removeEventListener("scroll", aoRolar);
      cabecalho.removeEventListener("focusin", aoFocar);
    };
  }, []);

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
    const perfilEscolhido = novoPerfilId === "cliente" ? "cliente" : "tatuador";
    const dados = perfilEscolhido === "cliente"
      ? { id: 1, nome: "Bruna", perfil: "cliente" }
      : { id: 2, nome: "Vitor", perfil: "tatuador" };

    definirUsuario(dados);
    definirTatuagemId(null);
    definirTelaAtual(perfilEscolhido === "cliente" ? "pedir" : "agenda");
    localStorage.setItem("pereiratatto-usuario", JSON.stringify(dados));
  }

  // Ao trocar de aba, os avisos da aba anterior deixam de valer.
  function trocarAba(aba) {
    definirAbaAtiva(aba);
    definirErroLogin("");
    definirErroCadastro("");
    definirMensagemCadastro("");
  }

  function fazerLogin(evento) {
    evento.preventDefault();
    definirEstadoLogin("carregando");
    definirErroLogin("");
    definirMensagemCadastro("");

    fetch(`${enderecoApi}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    })
      .then(async (resposta) => {
        const texto = await resposta.text();

        if (!resposta.ok) {
          let detalhe = "Credenciais inválidas.";
          try {
            const json = JSON.parse(texto);
            if (typeof json.detail === "string") {
              detalhe = json.detail;
            }
          } catch {
            detalhe = texto || detalhe;
          }
          throw new Error(detalhe);
        }

        if (!texto) {
          throw new Error("Resposta vazia da API.");
        }

        try {
          return JSON.parse(texto);
        } catch {
          throw new Error("A API respondeu em um formato inválido.");
        }
      })
      .then((resultado) => {
        localStorage.setItem("pereiratatto-token", resultado.access_token);
        localStorage.setItem("pereiratatto-usuario", JSON.stringify(resultado.usuario));
        definirUsuario(resultado.usuario);
        definirEmail("");
        definirSenha("");
        definirEstadoLogin("pronto");
        definirTelaAtual(resultado.usuario.perfil === "cliente" ? "pedir" : "agenda");
      })
      .catch((erro) => {
        const mensagem =
          erro?.message === "Failed to fetch"
            ? "Não foi possível conectar ao servidor. Verifique se a API está em execução e se a URL está correta."
            : erro?.message || "Não foi possível concluir o login.";

        definirErroLogin(mensagem);
        definirEstadoLogin("erro");
      });
  }

  function fazerCadastro(evento) {
    evento.preventDefault();
    definirErroCadastro("");
    definirMensagemCadastro("");

    if (senhaCadastro !== confirmacaoSenha) {
      definirErroCadastro("As senhas não coincidem.");
      definirEstadoCadastro("erro");
      return;
    }

    definirEstadoCadastro("carregando");

    fetch(`${enderecoApi}/cadastro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome, email: emailCadastro, senha: senhaCadastro }),
    })
      .then((resposta) => {
        if (!resposta.ok) {
          return resposta.json().then((detalhe) => {
            throw new Error(
              typeof detalhe.detail === "string"
                ? detalhe.detail
                : "Não foi possível criar a conta. Confira os dados informados."
            );
          });
        }
        return resposta.json();
      })
      .then(() => {
        definirMensagemCadastro("Conta criada com sucesso! Faça login para continuar.");
        definirNome("");
        definirEmail(emailCadastro);
        definirSenha("");
        definirEmailCadastro("");
        definirSenhaCadastro("");
        definirConfirmacaoSenha("");
        definirEstadoCadastro("pronto");
        definirAbaAtiva("login");
      })
      .catch((erro) => {
        const mensagem =
          erro?.message === "Failed to fetch"
            ? "Não foi possível conectar ao servidor. Verifique se a API está em execução e se a URL está correta."
            : erro?.message || "Não foi possível criar a conta.";

        definirErroCadastro(mensagem);
        definirEstadoCadastro("erro");
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
          <div className="auth-card">
            <div className="abas-login" role="tablist" aria-label="Acesso ao sistema">
              <button
                type="button"
                className={abaAtiva === "login" ? "aba-login ativa" : "aba-login"}
                role="tab"
                aria-selected={abaAtiva === "login"}
                onClick={() => trocarAba("login")}
              >
                Entrar
              </button>
              <button
                type="button"
                className={abaAtiva === "cadastro" ? "aba-login ativa" : "aba-login"}
                role="tab"
                aria-selected={abaAtiva === "cadastro"}
                onClick={() => trocarAba("cadastro")}
              >
                Criar conta
              </button>
            </div>

            {abaAtiva === "login" ? (
              <>
                <p className="sobretitulo">ACESSO AO SISTEMA</p>
                <h1>Entrar no PereiraTatto</h1>

                <form className="formulario" onSubmit={fazerLogin}>
                  <label className="campo-local-corpo">
                    E-mail
                    <input type="email" name="email" autoComplete="username" placeholder="seu@email.com" value={email} onChange={(evento) => definirEmail(evento.target.value)} required />
                  </label>
                  <label className="campo-local-corpo">
                    Senha
                    <input type="password" name="senha" autoComplete="current-password" value={senha} onChange={(evento) => definirSenha(evento.target.value)} required />
                  </label>
                  <button className="botao-principal" type="submit" disabled={estadoLogin === "carregando"}>
                    {estadoLogin === "carregando" ? "Entrando…" : "Entrar"}
                  </button>
                </form>
              </>
            ) : (
              <>
                <p className="sobretitulo">NOVA CONTA</p>
                <h2>Criar conta</h2>

                <form className="formulario" onSubmit={fazerCadastro}>
                  <label className="campo-local-corpo">
                    Nome
                    <input type="text" name="nome" autoComplete="name" placeholder="Seu nome" value={nome} onChange={(evento) => definirNome(evento.target.value)} required minLength={2} />
                  </label>
                  <label className="campo-local-corpo">
                    E-mail
                    <input type="email" name="email" autoComplete="email" placeholder="seu@email.com" value={emailCadastro} onChange={(evento) => definirEmailCadastro(evento.target.value)} required />
                  </label>
                  <label className="campo-local-corpo">
                    Senha
                    <input type="password" name="nova-senha" autoComplete="new-password" value={senhaCadastro} onChange={(evento) => definirSenhaCadastro(evento.target.value)} required minLength={8} maxLength={100} />
                    <small className="dica-campo">Use pelo menos 8 caracteres.</small>
                  </label>
                  <label className="campo-local-corpo">
                    Confirmar senha
                    <input type="password" name="confirmar-senha" autoComplete="new-password" value={confirmacaoSenha} onChange={(evento) => definirConfirmacaoSenha(evento.target.value)} required minLength={8} maxLength={100} />
                  </label>
                  <button className="botao-principal" type="submit" disabled={estadoCadastro === "carregando"}>
                    {estadoCadastro === "carregando" ? "Cadastrando…" : "Cadastrar conta"}
                  </button>
                </form>
              </>
            )}
          </div>

          <div className="auth-mensagens">
            {erroLogin && <p className="aviso erro" role="alert">{erroLogin}</p>}
            {erroCadastro && <p className="aviso erro" role="alert">{erroCadastro}</p>}
            {mensagemCadastro && <p className="aviso sucesso" role="status">{mensagemCadastro}</p>}
          </div>

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
      <header className="cabecalho" ref={cabecalhoRef}>
        <a className="marca" href="#inicio" onClick={() => definirTelaAtual(usuario?.perfil === "cliente" ? "pedir" : "agenda")}>
          Pereira<span>Tatto</span>
        </a>
        <p className="assinatura">ESTÚDIO DE TATUAGEM</p>

        {usuario && (
          <div className="seletor-perfil" role="group" aria-label="Sessão do usuário">
            <div className="opcoes-perfil">
              <button className="opcao-perfil ativa" type="button">
                <span className="icone-perfil" aria-hidden="true">{usuario.nome.charAt(0).toUpperCase()}</span>
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
