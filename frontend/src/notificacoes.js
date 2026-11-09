import { useCallback, useEffect, useRef, useState } from "react";

import { enderecoApi } from "./api.js";

// De quanto em quanto tempo o sistema confere se chegou mensagem nova, em qualquer tela.
// Continua consultando com a aba escondida, porque é justamente aí que o aviso do navegador ajuda.
const INTERVALO_NAO_LIDAS_MS = 5000;

// Hook é uma função que começa com "use" e reúne estado e efeitos para reaproveitar em componentes.
// Este acompanha as mensagens não lidas de quem está logado e chama aoChegarNova a cada mensagem nova.
export function useMensagensNaoLidas(usuario, aoChegarNova) {
  const [pendentes, definirPendentes] = useState([]);
  // Maior id de mensagem já visto em cada conversa. null indica que a primeira consulta ainda não voltou.
  const ultimasVistasRef = useRef(null);
  // Guarda sempre a versão mais nova da função, para o intervalo não usar uma cópia desatualizada.
  const aoChegarNovaRef = useRef(aoChegarNova);
  aoChegarNovaRef.current = aoChegarNova;
  const consultarRef = useRef(() => {});
  const usuarioId = usuario ? usuario.id : null;

  useEffect(() => {
    ultimasVistasRef.current = null;
    definirPendentes([]);
    if (usuarioId === null) return undefined;

    let ativo = true;
    let consultando = false;

    function consultar() {
      if (consultando) return;
      consultando = true;
      const token = localStorage.getItem("pereiratatto-token");

      fetch(`${enderecoApi}/mensagens/nao-lidas`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((resposta) => {
          if (!resposta.ok) throw new Error("Falha ao consultar mensagens não lidas.");
          return resposta.json();
        })
        .then((lista) => {
          if (!ativo) return;
          const anteriores = ultimasVistasRef.current;
          // Na primeira consulta só registra o que já existia: os contadores aparecem, mas sem aviso.
          const novas = anteriores === null
            ? []
            : lista.filter((item) => item.ultima_id > (anteriores.get(item.tatuagem_id) || 0));

          const atualizadas = new Map(anteriores || []);
          lista.forEach((item) => {
            atualizadas.set(item.tatuagem_id, Math.max(atualizadas.get(item.tatuagem_id) || 0, item.ultima_id));
          });
          ultimasVistasRef.current = atualizadas;

          definirPendentes(lista);
          novas.forEach((item) => aoChegarNovaRef.current(item));
        })
        // Uma falha de rede não deve atrapalhar a tela; a próxima consulta tenta de novo.
        .catch(() => {})
        .finally(() => {
          consultando = false;
        });
    }

    consultarRef.current = consultar;
    consultar();
    const intervalo = window.setInterval(consultar, INTERVALO_NAO_LIDAS_MS);

    return () => {
      ativo = false;
      window.clearInterval(intervalo);
      consultarRef.current = () => {};
    };
  }, [usuarioId]);

  // Permite pedir uma consulta na hora, por exemplo logo depois de ler uma conversa.
  // useCallback mantém a mesma função entre renderizações.
  const atualizar = useCallback(() => consultarRef.current(), []);
  const total = pendentes.reduce((soma, item) => soma + item.nao_lidas, 0);

  return { pendentes, total, atualizar };
}

// Diz se o navegador sabe mostrar notificações e qual foi a escolha da pessoa:
// "default" (ainda não perguntou), "granted" (permitiu), "denied" (bloqueou) ou "indisponivel".
export function permissaoNotificacao() {
  return "Notification" in window ? Notification.permission : "indisponivel";
}

// Pede a permissão. O navegador só aceita esse pedido a partir de um clique da pessoa.
export function pedirPermissaoNotificacao() {
  if (!("Notification" in window)) return Promise.resolve("indisponivel");
  return Notification.requestPermission();
}

// Mostra o aviso do sistema operacional, fora da página, quando a pessoa permitiu.
export function notificarNoNavegador(titulo, corpo, aoClicar) {
  if (permissaoNotificacao() !== "granted") return;
  try {
    // tag faz uma notificação nova da mesma conversa substituir a anterior em vez de empilhar.
    const notificacao = new Notification(titulo, { body: corpo, tag: titulo });
    notificacao.onclick = () => {
      window.focus();
      aoClicar();
      notificacao.close();
    };
  } catch {
    // Alguns celulares só mostram notificação por service worker; nesse caso fica o aviso dentro da página.
  }
}
