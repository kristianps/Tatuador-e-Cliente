import { useEffect, useState } from "react";

const etapas = ["pedida", "desenho aprovado", "em sessões", "finalizada"];

// Permite que o tatuador consulte todos os pedidos e filtre pela etapa atual.
function Agenda({ enderecoApi, aoAbrirFicha }) {
  // useState guarda o filtro, a lista e o estado da consulta à API.
  const [etapa, definirEtapa] = useState("");
  const [tatuagens, definirTatuagens] = useState([]);
  const [estado, definirEstado] = useState("carregando");
  const [erro, definirErro] = useState("");

  // useEffect consulta de novo quando a etapa muda, mantendo lista, carregamento e erro atualizados.
  useEffect(() => {
    definirEstado("carregando");
    definirErro("");
    const filtro = etapa ? `?etapa=${encodeURIComponent(etapa)}` : "";

    fetch(`${enderecoApi}/tatuagens${filtro}`)
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error("Não foi possível carregar a agenda.");
        }
        return resposta.json();
      })
      .then((lista) => {
        definirTatuagens(lista);
        definirEstado("pronto");
      })
      .catch((erroBusca) => {
        definirErro(erroBusca.message);
        definirEstado("erro");
      });
  }, [enderecoApi, etapa]);

  return (
    <section className="painel">
      <p className="sobretitulo">GESTÃO DO ESTÚDIO</p>
      <h1>A agenda</h1>
      <p className="introducao">Consulte os trabalhos e localize o próximo passo de cada tatuagem.</p>

      <label className="filtro-etapa">
        Filtrar por etapa
        <select value={etapa} onChange={(evento) => definirEtapa(evento.target.value)}>
          <option value="">Todas as etapas</option>
          {/* map cria uma opção para cada etapa definida pela cartilha. */}
          {etapas.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
      </label>

      {estado === "carregando" && <p className="estado-tela">Carregando agenda…</p>}
      {estado === "erro" && <p className="aviso erro" role="alert">{erro}</p>}
      {estado === "pronto" && tatuagens.length === 0 && (
        <div className="estado-vazio">Nenhuma tatuagem encontrada nesta etapa.</div>
      )}
      {estado === "pronto" && tatuagens.length > 0 && (
        <ul className="lista-tatuagens">
          {/* map apresenta um cartão para cada tatuagem retornada pela API. */}
          {tatuagens.map((tatuagem) => (
            <li className="cartao-tatuagem" key={tatuagem.id}>
              <div>
                <p className="identificador">TATUAGEM Nº {tatuagem.id}</p>
                <h2>{tatuagem.ideia}</h2>
                <p>Cliente {tatuagem.cliente_id} · {tatuagem.local_corpo} · {tatuagem.tamanho}</p>
                <span className="etapa">{tatuagem.etapa}</span>
              </div>
              <button className="botao-secundario" onClick={() => aoAbrirFicha(tatuagem.id)}>
                Abrir ficha
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default Agenda;
