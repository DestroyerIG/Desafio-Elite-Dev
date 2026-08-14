# Elite Events

## Visão geral

Plataforma full-stack de eventos e ingressos do Desafio Elite Dev 2026. O MVP será desenvolvido em fases e cobrirá publicação de eventos, reserva com proteção contra overselling, pagamento simulado, emissão de ingressos individuais, QR assinado, compartilhamento e validação na portaria.

Ao final da Fase 2, o repositório contém autenticação JWT com RBAC, catálogo externo da Ticketmaster, publicação de cópias locais de eventos e as experiências pública e do organizador no Next.js. Reservas, pagamentos, ingressos e portaria permanecem para as próximas fases.

## Arquitetura

O projeto é um monólito modular com frontend e backend implantáveis separadamente:

```text
Next.js -> FastAPI -> PostgreSQL
                 -> Ticketmaster Discovery API
```

Detalhes estão em [docs/architecture.md](docs/architecture.md).

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, TanStack Query e Zod.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2, Alembic, HTTPX, PyJWT e Argon2.
- Banco: PostgreSQL 16.
- Ambiente local: Docker Compose para o banco.

## Decisões técnicas

As decisões arquiteturais e seus trade-offs estão em [docs/decisions.md](docs/decisions.md).

## Como executar

Pré-requisitos: Docker, Python 3.12+ e Node.js 20.9+.

### Banco de dados

```powershell
docker compose up -d db
```

### Backend

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
python -m app.database.seed
uvicorn app.main:app --reload
```

A API estará em `http://localhost:8000`; `GET /health` verifica também a conexão com o PostgreSQL. A documentação OpenAPI fica em `http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

O frontend estará em `http://localhost:3000`.

## Variáveis de ambiente

Os arquivos `backend/.env.example` e `frontend/.env.example` documentam os valores necessários. Arquivos `.env` reais são ignorados pelo Git.

No backend, substitua `JWT_SECRET` por uma chave aleatória forte e informe `TICKETMASTER_API_KEY` para habilitar a busca no catálogo. A chave da Ticketmaster nunca é enviada ao frontend. Em produção, a aplicação rejeita o segredo JWT de desenvolvimento.

## Endpoints da Fase 2

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/me
GET    /api/v1/catalog/events?q=
GET    /api/v1/events
GET    /api/v1/events/{id}
POST   /api/v1/events
PATCH  /api/v1/events/{id}
DELETE /api/v1/events/{id}
GET    /api/v1/organizer/events
```

Cadastro público sempre cria um `CUSTOMER`. Pesquisa no catálogo e mutações de eventos exigem um JWT de `ORGANIZER`; a listagem e o detalhe de eventos publicados são públicos.

## Migrations

Execute migrations a partir de `backend/`:

```powershell
alembic upgrade head
alembic downgrade -1
```

## Seed

O seed é idempotente e cria quatro usuários de desenvolvimento. Ao encontrar os e-mails `.local` usados na Fase 1, ele os atualiza para os endereços válidos abaixo:

| Papel | E-mail | Senha local padrão |
|---|---|---|
| Organizador | `organizer@example.com` | `DevOnly123!` |
| Cliente | `customer1@example.com` | `DevOnly123!` |
| Cliente | `customer2@example.com` | `DevOnly123!` |
| Portaria | `gate@example.com` | `DevOnly123!` |

A senha pode ser alterada por `SEED_PASSWORD`. Essas credenciais existem somente para desenvolvimento e não devem ser usadas em produção.

## Testes

Instale as dependências de desenvolvimento e execute a suíte rápida:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
pytest -q
```

O teste ponta a ponta do backend é opt-in porque cria dados em um PostgreSQL isolado. Aponte `DATABASE_URL` para essa base, execute migration e seed, defina `RUN_INTEGRATION_TESTS=1` e rode `pytest -q` novamente. Nunca use uma base com dados importantes.

No frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Uso de IA

O uso de assistência por IA está descrito com transparência em [docs/ai-usage.md](docs/ai-usage.md).

## Trade-offs e limitações conhecidas

- O Compose executa apenas o PostgreSQL; backend e frontend rodam localmente para agilizar o desenvolvimento.
- O token JWT é mantido em `localStorage` neste MVP. Isso simplifica o cliente, mas exige disciplina contra XSS; uma evolução para produção pode usar cookie `HttpOnly` com proteção CSRF ou um BFF.
- Sem `TICKETMASTER_API_KEY`, o catálogo retorna um erro de configuração explícito; eventos locais publicados continuam disponíveis.
- Reservas, pagamentos, tickets e portaria ainda não estão implementados.
- Expiração automática de reservas, mapas de assento, filas, cache e pagamentos reais estão fora do MVP inicial.

## Melhorias futuras

As próximas fases seguirão a ordem: reservas e concorrência; pagamentos e tickets; portaria e compartilhamento; testes e qualidade; entrega.
