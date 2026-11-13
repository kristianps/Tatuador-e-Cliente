import { useEffect } from "react";

// Mostra uma foto em tela cheia por cima da página. Fecha com o botão, tocando fora da foto ou com Esc.
function VisualizadorFoto({ foto, aoFechar }) {
  // Esc fecha, como em qualquer janela sobreposta.
  useEffect(() => {
    function aoTeclar(evento) {
      if (evento.key === "Escape") aoFechar();
    }
    document.addEventListener("keydown", aoTeclar);
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [aoFechar]);

  return (
    // role="dialog" e aria-modal avisam ao leitor de tela que é uma janela por cima da página.
    <div className="visualizador-foto" role="dialog" aria-modal="true" aria-label="Foto ampliada" onClick={aoFechar}>
      <img src={foto} alt="Foto anexada, ampliada" onClick={(evento) => evento.stopPropagation()} />
      <button type="button" className="fechar-visualizador" aria-label="Fechar foto" onClick={aoFechar}>×</button>
    </div>
  );
}

export default VisualizadorFoto;
