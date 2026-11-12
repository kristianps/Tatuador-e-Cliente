import { useEffect, useState } from "react";

// Frases que se revezam no destaque da tela de entrada, falando do que o site oferece.
const frases = [
  "Sua ideia vira arte na pele.",
  "Acompanhe cada etapa, do desenho ao retoque.",
  "Converse com o tatuador sem sair do site.",
  "Peça sua tatuagem em poucos toques.",
];

// Só imagens em domínio público (CC0), que podem aparecer sem crédito na tela.
// Os autores estão em docs/CREDITOS_IMAGENS.md.
const fotos = [
  { arquivo: "dragao.jpg", nome: "Dragão" },
  { arquivo: "borboleta_a.jpg", nome: "Borboleta" },
  { arquivo: "ancora.jpg", nome: "Coração e âncora" },
  { arquivo: "adaga-foto.jpg", nome: "Adaga" },
  { arquivo: "aguia-foto.jpg", nome: "Águia" },
  { arquivo: "naval_recorte.jpg", nome: "Composição naval" },
];

// Traços da rosa desenhada na tela. Cada traço aparece um depois do outro, como uma agulha riscando a pele.
const tracosRosa = [
  "M100 70c-8-2-14 6-10 12 4 6 16 4 18-4 3-12-12-20-24-14-14 7-12 28 4 32 18 4 32-10 28-26-4-16-24-24-40-16",
  "M68 64c-14 10-16 34 2 45 16 9 40 8 52-4",
  "M132 58c17 8 21 32 7 46-10 10-26 14-40 12",
  "M70 104c6 18 26 26 44 22 14-3 24-12 26-24",
  "M104 128c-2 30 4 60-4 100",
  "M102 168c-18-14-40-10-50 4 16 8 36 8 50-4",
  "M101 196c16-16 38-14 48-2-14 10-34 12-48 2",
  "M103 150l9-6M100 214l-8-4",
];

// prefers-reduced-motion: a pessoa pediu ao aparelho para reduzir animações; respeitamos isso.
const reduzirMovimento = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Vitrine do estúdio na tela de entrada: frases, desenho animado e fotos de referência.
// É decorativa: o formulário de acesso funciona igual sem ela.
function VitrineEntrada() {
  const [indiceFrase, definirIndiceFrase] = useState(0);

  // Troca a frase a cada 3,8 segundos; com animações reduzidas, fica na primeira.
  useEffect(() => {
    if (reduzirMovimento()) return undefined;
    const intervalo = window.setInterval(() => {
      definirIndiceFrase((atual) => (atual + 1) % frases.length);
    }, 3800);
    return () => window.clearInterval(intervalo);
  }, []);

  return (
    <aside className="vitrine-entrada" aria-label="Apresentação do estúdio">
      {/* Desenho da rosa: aria-hidden porque é só enfeite. pathLength="1" deixa a animação igual para traços de tamanhos diferentes. */}
      <svg className="rosa-animada" viewBox="0 0 200 240" aria-hidden="true" focusable="false">
        {tracosRosa.map((traco, indice) => (
          <path key={traco} d={traco} pathLength="1" style={{ "--atraso": `${indice * 0.35}s` }} />
        ))}
      </svg>
      <span className="gota-tinta gota-1" aria-hidden="true" />
      <span className="gota-tinta gota-2" aria-hidden="true" />
      <span className="gota-tinta gota-3" aria-hidden="true" />

      <div className="vitrine-texto">
        <p className="vitrine-sobretitulo">Estúdio de tatuagem</p>
        <p className="vitrine-titulo">
          {/* Leitores de tela leem só a primeira frase, sem ouvir a troca a cada poucos segundos. */}
          <span className="somente-leitor">{frases[0]}</span>
          {/* key muda a cada troca, e o React recria o elemento: assim a animação de entrada roda de novo. */}
          <span className="frase-rotativa" key={indiceFrase} aria-hidden="true">{frases[indiceFrase]}</span>
        </p>
        <p className="vitrine-apoio">
          Do primeiro rascunho ao retoque final, tudo registrado num só lugar.
        </p>

        <ul className="vitrine-beneficios">
          <li style={{ "--atraso": "0.1s" }}>
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 20l4-1 11-11-3-3L5 16l-1 4zM14 6l3 3" /></svg>
            Peça online
          </li>
          <li style={{ "--atraso": "0.25s" }}>
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 12h4l2-5 4 10 2-5h4" /></svg>
            Acompanhe as etapas
          </li>
          <li style={{ "--atraso": "0.4s" }}>
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 18l-1 3 4-2h9a3 3 0 0 0 3-3V8a3 3 0 0 0-3-3H7a3 3 0 0 0-3 3v7a3 3 0 0 0 1 3z" /></svg>
            Fale com o estúdio
          </li>
        </ul>
      </div>

      {/* Esteira de fotos: a lista aparece duas vezes para o movimento emendar sem pulo. */}
      <div className="esteira-fotos">
        <ul className="esteira-trilho">
          {[...fotos, ...fotos].map((foto, indice) => (
            <li key={`${foto.arquivo}-${indice}`} aria-hidden={indice >= fotos.length}>
              <img src={`/decalques/${foto.arquivo}`} alt={indice < fotos.length ? `Referência de tatuagem: ${foto.nome}` : ""} loading="lazy" />
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

export default VitrineEntrada;
