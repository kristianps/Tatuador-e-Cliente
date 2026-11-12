import { useState } from "react";

// Campo de senha com o botão "olhinho", que mostra ou esconde o que foi digitado.
// Ajuda principalmente no celular, onde é fácil errar uma letra no teclado pequeno.
// ...propriedades repassa ao input tudo o que a tela informar (name, value, onChange, required...).
function CampoSenha(propriedades) {
  const [visivel, definirVisivel] = useState(false);

  return (
    <span className="entrada-senha">
      {/* Trocar o type de "password" para "text" é o que faz a senha aparecer. */}
      <input {...propriedades} type={visivel ? "text" : "password"} />
      <button
        className="botao-ver-senha"
        type="button"
        aria-label={visivel ? "Ocultar senha" : "Mostrar senha"}
        aria-pressed={visivel}
        // Impede que o toque tire o foco do campo; assim o teclado do celular não fecha.
        onMouseDown={(evento) => evento.preventDefault()}
        onClick={() => definirVisivel(!visivel)}
      >
        {visivel ? (
          // Olho riscado: a senha está à mostra e o toque volta a esconder.
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M3 3l18 18" />
            <path d="M10.6 5.1A10.4 10.4 0 0 1 12 5c6.5 0 10 7 10 7a17.6 17.6 0 0 1-3.2 4.2M6.6 6.6A17.4 17.4 0 0 0 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6" />
            <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
          </svg>
        ) : (
          // Olho aberto: o toque mostra a senha.
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
      </button>
    </span>
  );
}

export default CampoSenha;
