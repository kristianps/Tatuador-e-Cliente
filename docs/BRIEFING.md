# Briefing — PereiraTatto

> Rascunho para revisão. O texto parte da Cartilha 4 e deve ser ajustado às palavras do aluno antes da apresentação.

## Contexto

O PereiraTatto é um sistema para apoiar a organização de um estúdio de tatuagem. Hoje, as informações sobre cada trabalho ficam espalhadas em conversas, dificultando saber em que etapa está cada tatuagem e o que precisa acontecer em seguida.

## Pessoas atendidas

- **Bruna, cliente:** precisa pedir uma tatuagem e acompanhar a etapa e o histórico do próprio trabalho pelo celular.
- **Vitor, tatuador:** precisa consultar os trabalhos do estúdio, filtrar por etapa e registrar os passos realizados pelo computador.

## Objetivo

Centralizar os pedidos, as etapas e o histórico das tatuagens para que a cliente acompanhe o andamento e o tatuador organize os próximos passos.

**Justificativa:** esse objetivo responde ao problema da cartilha, que descreve informações perdidas em conversas e falta de clareza sobre a etapa de cada cliente.

## Escopo

- Pedir uma tatuagem informando ideia, local do corpo e tamanho.
- Consultar tatuagens por etapa e por cliente.
- Mostrar uma tatuagem e listar seu histórico de passos.
- Registrar desenho aprovado, sessão ou retoque.
- Atualizar a etapa conforme o passo aceito.

**Justificativa:** estas capacidades atendem às tarefas descritas para Bruna e Vitor na cartilha.

## Regra do processo

Uma tatuagem começa como **pedida**. O desenho precisa ser aprovado antes das sessões; pode haver uma ou mais sessões; e o retoque ocorre depois da cicatrização e de pelo menos uma sessão. Um passo aceito atualiza a etapa da tatuagem.

**Justificativa:** a sequência mantém no sistema a regra de negócio definida pela cartilha.

## Fora do escopo desta etapa

Orçamento, sinal, pagamento, portfólio com fotos, avisos por mensagem e login.

**Justificativa:** esses itens não fazem parte do que a Cartilha 4 pede para esta etapa do projeto.

## A aula 10 e o uso de IA no projeto

A aula apresentou uma etapa de planejamento: partir do briefing, identificar funcionalidades importantes, usar IA para revisar e estruturar o produto e transformar a ideia em um roadmap realista.

### O que foi apresentado

- o briefing é a base do projeto e expõe o problema e os usuários;
- a IA pode ajudar a encontrar lacunas, sugerir melhorias e priorizar recursos;
- o objetivo é integrar a ideia, a regra de negócio e a arquitetura antes de codificar;
- o roadmap organiza o que será entregue em cada fase.

### O que isso significa para o PereiraTatto

- manter a visão clara de cliente e tatuador;
- confirmar que a funcionalidade principal continua sendo o acompanhamento da tatuagem;
- separar o que é essencial para esta etapa do que pode vir depois;
- usar a IA como apoio para planejamento, revisão e alinhamento, não como substituto da regra do projeto.

### Roadmap sugerido

1. Etapa atual: autenticação, perfis e acompanhamento de tatuagem.
2. Próxima etapa: revisar fluxo de uso e integração frontend/backend.
3. Fase seguinte: melhorias de UX, validação das etapas e possíveis recursos de IA para organização e apoio.

**Conclusão:** a aula reforçou que a maior contribuição da IA aqui é ajudar a transformar a ideia em um plano melhor estruturado, e isso importa antes de qualquer implementação de código.
