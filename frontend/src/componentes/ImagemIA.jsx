import { useEffect, useState } from "react";

import { enderecoApi } from "../api.js";

// Mostra o rascunho criado com a IA para um pedido, se houver. Sem imagem, não mostra nada.
// Fica num componente à parte porque a imagem é buscada separada da lista de pedidos, que precisa ser leve.
function ImagemIA({ tatuagemId }) {
  const [imagem, definirImagem] = useState("");

  useEffect(() => {
    let ativo = true;
    definirImagem("");
    const token = localStorage.getItem("pereiratatto-token");
    fetch(`${enderecoApi}/tatuagens/${tatuagemId}/imagem-ia`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      // 404 é o caso normal de pedido sem imagem; não é erro para a tela.
      .then((resposta) => (resposta.ok ? resposta.json() : null))
      .then((dados) => {
        if (ativo && dados) definirImagem(dados.imagem);
      })
      .catch(() => {});
    return () => {
      ativo = false;
    };
  }, [tatuagemId]);

  if (!imagem) return null;

  return (
    <figure className="imagem-ia-pedido">
      <img src={imagem} alt="Imagem de referência anexada ao pedido" loading="lazy" />
      <figcaption>Imagem de referência do pedido</figcaption>
    </figure>
  );
}

export default ImagemIA;
