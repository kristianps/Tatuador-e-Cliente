import { useState } from "react";

import { enderecoApi } from "../api.js";
import CampoSenha from "../componentes/CampoSenha.jsx";

// Mostra o pedido do link por e-mail ou, quando a pessoa chega pelo link, a criação da nova senha.
function RecuperarSenha({ token, aoVoltar, aoRedefinir }) {
  const [email, definirEmail] = useState("");
  const [senha, definirSenha] = useState("");
  const [confirmacaoSenha, definirConfirmacaoSenha] = useState("");
  const [estado, definirEstado] = useState("pronto");
  const [erro, definirErro] = useState("");
  const [mensagem, definirMensagem] = useState("");

  // Envia os dados à API e devolve o erro em texto, pois a validação pode responder com uma lista.
  function enviar(caminho, dados, padraoDeErro) {
    return fetch(`${enderecoApi}${caminho}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then((resposta) =>
        resposta.json().then((corpo) => {
          if (!resposta.ok) {
            throw new Error(typeof corpo.detail === "string" ? corpo.detail : padraoDeErro);
          }
          return corpo;
        })
      )
      .catch((falha) => {
        throw new Error(
          falha?.message === "Failed to fetch"
            ? "Não foi possível conectar ao servidor. Tente novamente em instantes."
            : falha?.message || padraoDeErro
        );
      });
  }

  function pedirLink(evento) {
    evento.preventDefault();
    definirEstado("carregando");
    definirErro("");

    enviar("/recuperar-senha", { email }, "Confira o e-mail informado.")
      .then((resultado) => {
        definirMensagem(resultado.mensagem);
        definirEstado("pronto");
      })
      .catch((falha) => {
        definirErro(falha.message);
        definirEstado("erro");
      });
  }

  function salvarSenha(evento) {
    evento.preventDefault();
    definirErro("");

    if (senha !== confirmacaoSenha) {
      definirErro("As senhas não coincidem.");
      definirEstado("erro");
      return;
    }

    definirEstado("carregando");
    enviar("/redefinir-senha", { token, senha }, "Não foi possível alterar a senha.")
      .then(() => aoRedefinir())
      .catch((falha) => {
        definirErro(falha.message);
        definirEstado("erro");
      });
  }

  return (
    <div className="auth-card">
      <button className="link-voltar" type="button" onClick={aoVoltar}>← Voltar para o login</button>

      {token ? (
        <>
          <p className="sobretitulo">NOVA SENHA</p>
          <h2>Criar nova senha</h2>

          <form className="formulario" onSubmit={salvarSenha}>
            <div className="linha-campos">
              <label className="campo-local-corpo">
                Nova senha
                <CampoSenha name="nova-senha" autoComplete="new-password" value={senha} onChange={(evento) => definirSenha(evento.target.value)} required minLength={8} maxLength={100} />
                <small className="dica-campo">Use pelo menos 8 caracteres.</small>
              </label>
              <label className="campo-local-corpo">
                Confirmar senha
                <CampoSenha name="confirmar-senha" autoComplete="new-password" value={confirmacaoSenha} onChange={(evento) => definirConfirmacaoSenha(evento.target.value)} required minLength={8} maxLength={100} />
              </label>
            </div>
            <button className="botao-principal" type="submit" disabled={estado === "carregando"}>
              {estado === "carregando" ? "Salvando…" : "Salvar nova senha"}
            </button>
          </form>
        </>
      ) : (
        <>
          <p className="sobretitulo">RECUPERAR ACESSO</p>
          <h2>Esqueceu sua senha?</h2>

          {mensagem ? (
            <p className="aviso sucesso" role="status">{mensagem} Confira também a caixa de spam.</p>
          ) : (
            <>
              <p className="dica-campo">Informe seu e-mail e enviaremos um link para criar uma nova senha.</p>
              <form className="formulario" onSubmit={pedirLink}>
                <label className="campo-local-corpo">
                  E-mail
                  <input type="email" name="email" autoComplete="email" placeholder="seu@email.com" value={email} onChange={(evento) => definirEmail(evento.target.value)} required />
                </label>
                <button className="botao-principal" type="submit" disabled={estado === "carregando"}>
                  {estado === "carregando" ? "Enviando…" : "Enviar link"}
                </button>
              </form>
            </>
          )}
        </>
      )}

      {erro && <p className="aviso erro" role="alert">{erro}</p>}
    </div>
  );
}

export default RecuperarSenha;
