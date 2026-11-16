import { useEffect, useState } from "react";

import { enderecoApi } from "../api.js";

// Mostra o rascunho criado com a IA para um pedido, se houver. Sem imagem, não mostra nada.
// Fica num componente à parte porque a imagem é buscada separada da lista de pedidos, que precisa ser leve.
function ImagemIA({ tatuagemId }) {
  const [imagens, definirImagens] = useState([]);

  useEffect(() => {
    let ativo = true;
    definirImagens([]);
    const token = localStorage.getItem("pereiratatto-token");
    fetch(`${enderecoApi}/tatuagens/${tatuagemId}/imagens-ia`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      // 404 é o caso normal de pedido sem imagem; não é erro para a tela.
      .then((resposta) => (resposta.ok ? resposta.json() : null))
      .then((dados) => {
        if (ativo && dados) definirImagens(dados.imagens || []);
      })
      .catch(() => {});
    return () => {
      ativo = false;
    };
  }, [tatuagemId]);

  if (!imagens.length) return null;

  return (
    <div className="propostas-ia-pedido">
      <h3>Propostas criadas com IA</h3>
      <p>Rascunhos para comparação e avaliação do tatuador.</p>
      {imagens.map((imagem, indice) => (
        <figure className="imagem-ia-pedido" key={indice}>
          <img src={imagem} alt={`Proposta ${indice + 1} de referência do pedido`} loading="lazy" />
          <figcaption>Proposta {indice + 1} · referência para revisão do tatuador</figcaption>
        </figure>
      ))}
    </div>
  );
}

export default ImagemIA;
