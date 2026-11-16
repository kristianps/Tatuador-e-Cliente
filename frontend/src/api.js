const backendLocal = "http://127.0.0.1:8000";
const backendAlternativo = "http://localhost:8000";
const backendProdução = "https://backend-two-gray-28.vercel.app";

const enderecoApi =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.MODE === "production" ? backendProdução : backendLocal) ||
  backendAlternativo;

// Avisado quando a API recusa o token (vencido, inválido ou de uma conta apagada).
// A Aplicacao escuta este evento e encerra a sessão, em vez de cada tela mostrar um erro diferente.
const EVENTO_SESSAO_EXPIRADA = "pereiratatto:sessao-expirada";

const MENSAGEM_SEM_CONEXAO =
  "Não foi possível conectar ao servidor. Verifique sua internet e tente de novo em instantes.";

// Ponto único de conversa com a API: coloca o token do login, transforma o corpo em JSON
// e trata a falta de conexão e o token recusado do mesmo jeito em todas as telas.
// Devolve a resposta do fetch, então cada tela continua conferindo resposta.ok como antes.
// "publica" é para login, cadastro e recuperação de senha, que não usam token.
function requisitar(caminho, { metodo = "GET", corpo, publica = false } = {}) {
  const token = publica ? null : localStorage.getItem("pereiratatto-token");
  const cabecalhos = {};
  if (corpo !== undefined) cabecalhos["Content-Type"] = "application/json";
  if (token) cabecalhos.Authorization = `Bearer ${token}`;

  return fetch(`${enderecoApi}${caminho}`, {
    method: metodo,
    headers: cabecalhos,
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  }).then(
    (resposta) => {
      // 401 com token enviado quer dizer sessão inválida; sem token, é só senha errada no login.
      if (resposta.status === 401 && token) {
        window.dispatchEvent(new Event(EVENTO_SESSAO_EXPIRADA));
      }
      return resposta;
    },
    // O fetch só falha sozinho quando não chega ao servidor (sem internet, API fora do ar).
    () => {
      throw new Error(MENSAGEM_SEM_CONEXAO);
    },
  );
}

// Lê a mensagem de erro que a API mandou (campo "detail"), ou usa a mensagem padrão da tela.
async function lerErro(resposta, padrao) {
  const dados = await resposta.json().catch(() => ({}));
  return typeof dados.detail === "string" ? dados.detail : padrao;
}

export { enderecoApi, EVENTO_SESSAO_EXPIRADA, lerErro, requisitar };
export default enderecoApi;
