// Ferramentas para fotos anexadas na conversa e na assistente.

// Tipos de foto aceitos, os mesmos que a API aceita.
export const TIPOS_ACEITOS = "image/jpeg,image/png,image/webp";

// Reduz a imagem para no máximo `ladoMaximo` px e converte para JPEG.
// Foto de celular passa fácil de 3 MB; reduzida, fica em torno de 150 KB, leve para enviar e guardar.
// canvas é uma área de desenho do navegador: a imagem é desenhada menor e exportada de novo.
export function reduzirImagem(dataUrl, ladoMaximo = 1280) {
  return new Promise((resolver, rejeitar) => {
    const imagem = new Image();
    imagem.onload = () => {
      const escala = Math.min(1, ladoMaximo / Math.max(imagem.width, imagem.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(imagem.width * escala);
      canvas.height = Math.round(imagem.height * escala);
      const contexto = canvas.getContext("2d");
      // Fundo branco: o JPEG não tem transparência.
      contexto.fillStyle = "#ffffff";
      contexto.fillRect(0, 0, canvas.width, canvas.height);
      contexto.drawImage(imagem, 0, 0, canvas.width, canvas.height);
      resolver(canvas.toDataURL("image/jpeg", 0.82));
    };
    imagem.onerror = () => rejeitar(new Error("Não foi possível abrir esta imagem. Tente outra foto."));
    imagem.src = dataUrl;
  });
}

// Lê o arquivo escolhido pela pessoa e devolve a foto já reduzida, como data URL.
// FileReader é a ferramenta do navegador que lê um arquivo do aparelho sem enviá-lo a lugar nenhum.
export function lerFoto(arquivo) {
  if (!arquivo) return Promise.reject(new Error("Nenhuma foto escolhida."));
  if (!TIPOS_ACEITOS.split(",").includes(arquivo.type)) {
    return Promise.reject(new Error("Envie uma foto em JPG, PNG ou WebP."));
  }
  return new Promise((resolver, rejeitar) => {
    const leitor = new FileReader();
    leitor.onload = () => reduzirImagem(leitor.result).then(resolver, rejeitar);
    leitor.onerror = () => rejeitar(new Error("Não foi possível ler esta foto."));
    leitor.readAsDataURL(arquivo);
  });
}
