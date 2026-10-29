# Arquitetura de produção (proposta)

## 1. Arquitetura de produção

```mermaid
flowchart LR
    usuario["Navegador\nCliente"] -->|HTTPS 443| tela["Tela na Vercel\nReact/Vite"]
    tela -->|HTTPS 443\n/api/:caminho*| api["API na Vercel\nFastAPI"]
    api -->|PostgreSQL SSL/TLS\nTransaction Pooler 6543| supabase["Supabase\nPostgreSQL"]

    tela -. "rewrite do front para a API" .-> api
    api -. "consulta e grava dados no banco" .-> supabase
```

Para testar no Mermaid Live, cole apenas o conteúdo do bloco, começando em `flowchart LR`.

Linhas por caixa:
- Navegador: roda na máquina do usuário; acessa a tela pública no domínio da Vercel via HTTPS na porta 443.
- Tela na Vercel: a interface React fica em um projeto Vercel com root directory `frontend`; ela recebe o tráfego público e usa rewrite para a API pública em `/api`.
- API na Vercel: o backend FastAPI fica em um projeto separado do Vercel com root directory `backend`; recebe requisições HTTPS da tela e fala com o banco via `URL_DO_BANCO` do Supabase.
- Banco no Supabase: o PostgreSQL fica fora do Vercel, em um projeto Supabase; a API usa o Transaction Pooler e autentica com a URL de conexão do banco.
- Protocolo: a tela conversa com a API em HTTPS e a API conversa com o banco em PostgreSQL com SSL/TLS.

## 2. Desenvolvimento e produção

| Componente | Desenvolvimento local | Produção (Vercel + Supabase) |
|---|---|---|
| API | `fastapi dev main.py` em `http://127.0.0.1:8000` | Projeto Vercel separado com `Root Directory: backend` |
| Tela | `npm run dev` em `http://127.0.0.1:5173` | Projeto Vercel separado com `Root Directory: frontend` |
| Banco | SQLite local ou MySQL local | Supabase PostgreSQL usando `URL_DO_BANCO` |
| `.env` | `backend/.env` local | Variáveis de ambiente do projeto Vercel e do Supabase |
| CORS | Permite origens locais | A tela e a API ficam em domínios públicos separados; o rewrite da Vercel direciona o tráfego para a API |
| Conexão | Host local, porta local | URL do Transaction Pooler do Supabase |

Observações:
- A arquitetura nova segue a proposta de dois projetos Vercel: um para a tela e um para a API.
- A tela chama a API pelo caminho `/api`, e o `vercel.json` faz o rewrite para o domínio da API pública.
- A API conversa com o banco por SQLAlchemy usando a variável `URL_DO_BANCO`.
- A troca do banco exige sair do padrão MySQL e passar a usar strings de conexão do PostgreSQL do Supabase.

## 3. O caminho do login

1. O usuário abre o navegador e acessa a tela pública hospedada na Vercel.  
   Máquina: usuário.

2. O navegador envia uma requisição `POST` para `/api/login` pela URL pública do front.  
   Máquina: usuário envia; Vercel recebe o tráfego do front.

3. O `frontend/vercel.json` faz o rewrite de `/api/:caminho*` para o domínio da API na Vercel.  
   Máquina: Vercel.

4. A API pública na Vercel recebe a requisição e chama a rota de autenticação do FastAPI.  
   Máquina: Vercel.

5. A API consulta o banco no Supabase e valida e-mail e senha do usuário.  
   Máquina: API e banco.

6. Se a autenticação for válida, a API gera o token e retorna os dados do usuário.  
   Máquina: API.

7. O navegador guarda o token no `localStorage` e usa esse valor nas próximas requisições protegidas.  
   Máquina: usuário.

8. Nas requisições seguintes, a API valida o token e responde com os dados solicitados.  
   Máquina: Vercel e Supabase.

## 4. O que muda no deploy

- `frontend`: project root `frontend`; o `vercel.json` redireciona `/api/:caminho*` para o domínio da API.
- `backend`: project root `backend`; a Vercel reconhece o `main.py` e faz o deploy da API.
- Banco: `URL_DO_BANCO` aponta para o Transaction Pooler do Supabase, com `sslmode=require`.
- Ambiente: a API usa o PostgreSQL do Supabase e não mais a conexão em peças do MySQL local.

## 5. Como testar a troca

1. Preencha `URL_DO_BANCO` no arquivo local `.env` do `backend`, usando o Transaction Pooler do Supabase.  
2. Codifique caracteres especiais da senha antes de montar a URL: use percent-encoding, como `@` -> `%40`, `#` -> `%23`, `!` -> `%21`, `:` -> `%3A`, `/` -> `%2F`, `?` -> `%3F`, `&` -> `%26`, `=` -> `%3D`.
3. Verifique o formato geral: `postgresql://postgres:senha%40codificada@db.<project-ref>.supabase.co:6543/postgres?sslmode=require`.
4. Rode `python criar_tabelas.py` dentro do diretório do backend.
5. Só se o comando terminar sem erro, rode `alembic stamp head`.
6. Abra o Supabase, vá ao Table Editor e confira as tabelas criadas.
7. Ative o RLS nas tabelas que forem sensíveis.
8. Inicie a API com `fastapi dev` e teste o login de cada perfil.
9. Valide o fluxo do cliente e do tatuador separadamente.

## 6. Observações finais

- O projeto atual ainda continha pontos específicos de MySQL; a troca para PostgreSQL exige revisar todas as strings de conexão e os comandos SQL específicos.
- A API continua sendo a camada responsável pela validação, autenticação e escrita no banco.
- A tela continua sendo um cliente web, sem conter a senha nem a chave do banco em código.
