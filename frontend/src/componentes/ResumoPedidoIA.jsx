import { useState } from "react";

// Transforma o texto digitado em lista: elementos separados por vírgula, perguntas uma por linha.
function paraLista(texto, separador) {
  return texto.split(separador).map((item) => item.trim()).filter(Boolean);
}

// Resumo do pedido montado pela IA a partir da conversa com a assistente.
// Com "editavel", a cliente corrige os campos antes de enviar; sem ele, só mostra (ficha e histórico).
function ResumoPedidoIA({ resumo, editavel = false, aoMudar, aoRemover }) {
  // As listas ficam como texto enquanto a cliente digita, para a vírgula e a quebra de linha não sumirem no meio.
  const [elementosTexto, definirElementosTexto] = useState((resumo?.elementos || []).join(", "));
  const [pendenciasTexto, definirPendenciasTexto] = useState((resumo?.pendencias || []).join("\n"));

  if (!resumo) return null;

  const { estilo, elementos = [], significado, cores, pendencias = [] } = resumo;
  const temConteudo = estilo || elementos.length || significado || cores || pendencias.length;

  if (!editavel) {
    if (!temConteudo) return null;
    return (
      <section className="resumo-ia" aria-label="Resumo do pedido feito com a assistente">
        <p className="resumo-ia-selo">Resumo da conversa com a assistente</p>
        <dl className="resumo-ia-campos">
          {estilo && <div><dt>Estilo</dt><dd>{estilo}</dd></div>}
          {cores && <div><dt>Cores</dt><dd>{cores}</dd></div>}
          {significado && <div className="resumo-ia-largo"><dt>Significado</dt><dd>{significado}</dd></div>}
          {elementos.length > 0 && (
            <div className="resumo-ia-largo">
              <dt>Elementos</dt>
              <dd>
                <ul className="resumo-ia-etiquetas">
                  {elementos.map((elemento) => <li key={elemento}>{elemento}</li>)}
                </ul>
              </dd>
            </div>
          )}
        </dl>
        {pendencias.length > 0 && (
          <div className="resumo-ia-pendencias">
            <h3>O que falta definir</h3>
            <ul>
              {pendencias.map((pergunta) => <li key={pergunta}>{pergunta}</li>)}
            </ul>
          </div>
        )}
      </section>
    );
  }

  function mudar(campo, valor) {
    aoMudar({ ...resumo, [campo]: valor });
  }

  return (
    <section className="resumo-ia resumo-ia-editavel" aria-label="Resumo do pedido para revisar">
      <div className="resumo-ia-topo">
        <div>
          <p className="resumo-ia-selo">Resumo da conversa com a assistente</p>
          <p className="resumo-ia-ajuda">Confira e corrija o que precisar. O tatuador recebe este resumo junto com o pedido.</p>
        </div>
        <button className="botao-secundario" type="button" onClick={aoRemover}>Remover</button>
      </div>

      <div className="resumo-ia-formulario">
        <label>
          Estilo
          <input value={estilo || ""} maxLength={120} onChange={(evento) => mudar("estilo", evento.target.value)} placeholder="Ex.: fineline" />
        </label>
        <label>
          Cores
          <input value={cores || ""} maxLength={120} onChange={(evento) => mudar("cores", evento.target.value)} placeholder="Ex.: preto e cinza" />
        </label>
        <label className="resumo-ia-largo">
          Elementos <small>(separe por vírgula)</small>
          <input
            value={elementosTexto}
            onChange={(evento) => {
              definirElementosTexto(evento.target.value);
              mudar("elementos", paraLista(evento.target.value, ",").slice(0, 8));
            }}
            placeholder="Ex.: lua, lavanda"
          />
        </label>
        <label className="resumo-ia-largo">
          Significado
          <input value={significado || ""} maxLength={300} onChange={(evento) => mudar("significado", evento.target.value)} placeholder="Ex.: homenagem à minha avó" />
        </label>
        <label className="resumo-ia-largo">
          O que falta definir <small>(uma pergunta por linha)</small>
          <textarea
            rows={3}
            value={pendenciasTexto}
            onChange={(evento) => {
              definirPendenciasTexto(evento.target.value);
              mudar("pendencias", paraLista(evento.target.value, "\n").slice(0, 5));
            }}
          />
        </label>
      </div>
    </section>
  );
}

export default ResumoPedidoIA;
