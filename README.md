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
pip install "fastapi[standard]" python-dotenv
if (-not (Test-Path .env)) { Copy-Item .env.exemplo .env }
```

Abra `backend/.env` e confira se `FRONTEND_ORIGEM` está como `http://127.0.0.1:5173`. Depois, ainda dentro de `backend/`, inicie a API:

```powershell
fastapi dev main.py
```

A documentação interativa da API fica em [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Como executar o frontend

Em outro terminal PowerShell, a partir da raiz do repositório:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Abra [http://127.0.0.1:5173](http://127.0.0.1:5173). Escolha Bruna para pedir e acompanhar tatuagens ou Vitor para consultar a agenda e registrar passos.

## Fluxo manual para conferir a aplicação

1. Com os dois servidores ligados, escolha Bruna, selecione uma ou mais refer?ncias visuais e escolha a regiao do corpo no menu.
2. Em **Minhas tatuagens**, confira a etapa inicial e abra o histórico.
3. Escolha Vitor, abra **A agenda** e selecione a tatuagem.
4. Na ficha, registre o desenho aprovado e depois uma ou mais sessões.
5. Após a cicatrização, registre o retoque e confira a etapa **finalizada**.
6. Volte para Bruna e consulte o histórico atualizado.

Os dados ficam em listas na memória e são apagados quando o backend é reiniciado. A cartilha não define um campo ou passo separado para registrar a cicatrização; por isso, Vitor confirma esse momento antes de registrar o retoque. O backend confere que já houve pelo menos uma sessão.

## Documentos do projeto

- [Cartilha](docs/CARTILHA.md)
- [Briefing](docs/BRIEFING.md)
- [Styleguide](docs/styleguide/STYLEGUIDE.md)
- [Cr�ditos e licen�as das imagens](docs/CREDITOS_IMAGENS.md)
- [Conceito da marca](docs/marca/pereiratatto-conceito.svg)
