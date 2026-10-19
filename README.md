# PereiraTatto

Sistema de acompanhamento das tatuagens do estúdio Traço Fino, baseado na Cartilha 4.

## Estrutura

- `docs/`: cartilha, briefing, marca e styleguide.
- `frontend/`: aplicação React com as quatro telas da cartilha.
- `backend/`: API FastAPI organizada em rotas, serviços, repositórios e esquemas.

## Requisitos

- Python 3.10 ou superior.
- Node.js 20.19+ ou 22.12+ para a versão atual do Vite.

## Como executar o backend

No PowerShell, a partir da raiz do repositório:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install "fastapi[standard]" python-dotenv mysql-connector-python PyJWT
if (-not (Test-Path .env)) { Copy-Item .env.exemplo .env }
```

Abra `backend/.env` e confira se `FRONTEND_ORIGEM` está como `http://127.0.0.1:5173`. Depois, ainda dentro de `backend/`, inicie a API:

```powershell
fastapi dev main.py
```

A documentação interativa da API fica em [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Login do sistema

O sistema agora usa autenticação por e-mail e senha. A API cria os usuários de demonstração automaticamente quando inicia:

- Bruna — cliente — bruna@pereiratatto.com / bruna123
- Vitor — tatuador — vitor@pereiratatto.com / vitor123

Ao logar, a API retorna um token JWT que o frontend salva no `localStorage` e envia em `Authorization: Bearer ...` nas requisições protegidas.

## Como executar o frontend

Em outro terminal PowerShell, a partir da raiz do repositório:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Abra [http://127.0.0.1:5173](http://127.0.0.1:5173). A tela inicial agora pede login com e-mail e senha antes de exibir as áreas do cliente ou tatuador.

## Fluxo manual para conferir a aplicação

1. Faça login com Bruna e envie uma ou mais referências visuais e a região do corpo.
2. Em **Minhas tatuagens**, confira a etapa inicial e abra o histórico.
3. Faça logout e entre como Vitor para consultar a agenda e registrar passos.
4. Na ficha, registre o desenho aprovado e depois uma ou mais sessões.
5. Após a cicatrização, registre o retoque e confira a etapa **finalizada**.
6. Volte para Bruna e consulte o histórico atualizado.

Os dados ficam em MySQL local e são persistidos enquanto o banco estiver ativo. O backend valida a sessão por token e cada perfil tem acesso de acordo com sua autenticação.

## Documentos do projeto

- [Cartilha](docs/CARTILHA.md)
- [Briefing](docs/BRIEFING.md)
- [Styleguide](docs/styleguide/STYLEGUIDE.md)
- [Créditos e licenças das imagens](docs/CREDITOS_IMAGENS.md)
- [Conceito da marca](docs/marca/pereiratatto-conceito.svg)
