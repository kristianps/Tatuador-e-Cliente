import { useEffect, useState } from "react";

import { enderecoApi } from "../api.js";

// Cabeçalhos com o token do login; as rotas de clientes só aceitam o tatuador.
function cabecalhosComToken(extras = {}) {
  const token = localStorage.getItem("pereiratatto-token");
  return token ? { ...extras, Authorization: `Bearer ${token}` } : extras;
}

// Aba do tatuador para cadastrar quem vem pessoalmente ao estúdio e consultar todas as clientes.
function Clientes() {
  const [clientes, definirClientes] = useState([]);
  const [estadoLista, definirEstadoLista] = useState("carregando");
  const [erroLista, definirErroLista] = useState("");
  const [busca, definirBusca] = useState("");

  const [nome, definirNome] = useState("");
  const [email, definirEmail] = useState("");
  const [telefone, definirTelefone] = useState("");
  const [estadoCadastro, definirEstadoCadastro] = useState("pronto");
  const [erroCadastro, definirErroCadastro] = useState("");
  // Guarda a cliente recém-criada e a senha provisória, mostrada só nesta tela e só uma vez.
  const [criada, definirCriada] = useState(null);
  const [copiada, definirCopiada] = useState(false);

  // Busca a lista de clientes ao abrir a aba.
  function carregarClientes() {
    fetch(`${enderecoApi}/clientes`, { headers: cabecalhosComToken() })
      .then((resposta) => {
        if (!resposta.ok) throw new Error("Não foi possível carregar as clientes.");
        return resposta.json();
      })
      .then((lista) => {
        definirClientes(lista);
        definirEstadoLista("pronto");
      })
      .catch((erro) => {
        definirErroLista(erro.message);
        definirEstadoLista("erro");
      });
  }

  useEffect(carregarClientes, []);

  // Envia o cadastro presencial; a API cria a conta de cliente e devolve a senha provisória.
  function cadastrar(evento) {
    evento.preventDefault();
    definirEstadoCadastro("carregando");
    definirErroCadastro("");
    definirCriada(null);
    definirCopiada(false);

    fetch(`${enderecoApi}/clientes`, {
      method: "POST",
      headers: cabecalhosComToken({ "Content-Type": "application/json" }),
      body: JSON.stringify({ nome: nome.trim(), email: email.trim(), telefone: telefone.trim() }),
    })
      .then(async (resposta) => {
        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) {
          // 400 traz o motivo em texto (e-mail já cadastrado); 422 traz uma lista de campos inválidos.
          throw new Error(typeof corpo.detail === "string" ? corpo.detail : "Confira o nome, o e-mail e o telefone.");
        }
        return corpo;
      })
      .then((resultado) => {
        definirCriada(resultado);
        definirClientes((atuais) => [resultado.cliente, ...atuais]);
        definirNome("");
        definirEmail("");
        definirTelefone("");
        definirEstadoCadastro("pronto");
      })
      .catch((erro) => {
        definirErroCadastro(erro.message);
        definirEstadoCadastro("erro");
      });
  }

  // Copia a senha para o tatuador colar numa mensagem, se preferir enviar em vez de anotar.
  function copiarSenha() {
    navigator.clipboard
      .writeText(criada.senha_provisoria)
      .then(() => definirCopiada(true))
      .catch(() => definirCopiada(false));
  }

  // Filtra por nome, e-mail ou telefone, sem diferenciar maiúsculas de minúsculas.
  const termo = busca.trim().toLocaleLowerCase("pt-BR");
  const filtradas = clientes.filter((cliente) =>
    `${cliente.nome} ${cliente.email} ${cliente.telefone || ""}`.toLocaleLowerCase("pt-BR").includes(termo),
  );
  const presenciais = clientes.filter((cliente) => cliente.origem === "presencial").length;

  return (
    <section className="painel painel-clientes">
      <p className="sobretitulo">ESTÚDIO PEREIRATATTO</p>
      <h1>Clientes</h1>
      <p className="introducao">Cadastre quem veio pessoalmente e consulte todas as clientes do estúdio.</p>

      <div className="area-clientes">
        <section className="bloco-cadastro-presencial" aria-labelledby="titulo-presencial">
          <h2 id="titulo-presencial">Cadastro presencial</h2>
          <p className="ajuda-campo">Para quem veio ao estúdio sem passar pelo site.</p>

          <form className="formulario" onSubmit={cadastrar}>
            <label>
              Nome
              <input type="text" autoComplete="off" value={nome} onChange={(evento) => definirNome(evento.target.value)} required minLength={2} maxLength={120} />
            </label>
            <label>
              E-mail
              <input type="email" autoComplete="off" value={email} onChange={(evento) => definirEmail(evento.target.value)} required />
              <span className="ajuda-campo">É o login da cliente no site.</span>
            </label>
            <label>
              {/* O rótulo do formulário é uma grade; o span mantém "Telefone (opcional)" na mesma linha. */}
              <span>Telefone <span className="opcional">(opcional)</span></span>
              {/* type="tel" abre o teclado de telefone no celular. */}
              <input type="tel" autoComplete="off" placeholder="(48) 99999-9999" value={telefone} onChange={(evento) => definirTelefone(evento.target.value)} maxLength={30} />
            </label>
            <button className="botao-principal" type="submit" disabled={estadoCadastro === "carregando"}>
              {estadoCadastro === "carregando" ? "Cadastrando…" : "Cadastrar cliente"}
            </button>
          </form>

          {estadoCadastro === "erro" && <p className="aviso erro" role="alert">{erroCadastro}</p>}

          {criada && (
            <div className="senha-provisoria" role="status">
              <p><strong>{criada.cliente.nome}</strong> foi cadastrada.</p>
              <p>Entregue o login e a senha provisória a ela:</p>
              <dl>
                <dt>E-mail</dt>
                <dd>{criada.cliente.email}</dd>
                <dt>Senha provisória</dt>
                <dd className="codigo-senha">{criada.senha_provisoria}</dd>
              </dl>
              <button className="botao-secundario" type="button" onClick={copiarSenha}>
                {copiada ? "Senha copiada" : "Copiar senha"}
              </button>
              <p className="ajuda-campo">
                A senha aparece só agora. Depois, a cliente cria a senha dela em “Esqueci minha senha”, na tela de login.
              </p>
            </div>
          )}
        </section>

        <section className="bloco-lista-clientes" aria-labelledby="titulo-lista-clientes">
          <div className="cabecalho-lista-clientes">
            <h2 id="titulo-lista-clientes">Clientes cadastradas</h2>
            {/* A contagem só aparece depois que a lista chega, para não mostrar "0" enquanto carrega. */}
            {estadoLista === "pronto" && (
              <span className="selo-contagem">{clientes.length} no total · {presenciais} presenciais</span>
            )}
          </div>

          <label className="busca-agenda">
            Buscar cliente
            <input type="search" placeholder="Nome, e-mail ou telefone" value={busca} onChange={(evento) => definirBusca(evento.target.value)} />
          </label>

          {estadoLista === "carregando" && <p className="estado-tela">Carregando clientes…</p>}
          {estadoLista === "erro" && <p className="aviso erro" role="alert">{erroLista}</p>}
          {estadoLista === "pronto" && filtradas.length === 0 && (
            <div className="estado-vazio">{clientes.length === 0 ? "Nenhuma cliente cadastrada ainda." : "Nenhuma cliente encontrada."}</div>
          )}

          {estadoLista === "pronto" && filtradas.length > 0 && (
            <ul className="lista-clientes">
              {filtradas.map((cliente) => (
                <li className="cartao-cliente" key={cliente.id}>
                  <div className="cartao-cliente-topo">
                    <strong>{cliente.nome}</strong>
                    {/* A origem aparece em texto, não só pela cor. */}
                    <span className={cliente.origem === "presencial" ? "etiqueta-origem presencial" : "etiqueta-origem"}>
                      {cliente.origem === "presencial" ? "Presencial" : "Site"}
                    </span>
                  </div>
                  <span className="cartao-cliente-dado">{cliente.email}</span>
                  {cliente.telefone && (
                    // tel: abre a discagem quando tocado no celular.
                    <a className="cartao-cliente-dado" href={`tel:${cliente.telefone.replace(/[^0-9+]/g, "")}`}>{cliente.telefone}</a>
                  )}
                  <span className="cartao-cliente-pedidos">
                    {cliente.pedidos === 1 ? "1 pedido" : `${cliente.pedidos} pedidos`}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </section>
  );
}

export default Clientes;
