# Elite Events

## Visão geral

Plataforma full-stack de eventos e ingressos do Desafio Elite Dev 2026. O MVP será desenvolvido em fases e cobrirá publicação de eventos, reserva com proteção contra overselling, pagamento simulado, emissão de ingressos individuais, QR assinado, compartilhamento e validação na portaria.

Nesta primeira fase, o repositório contém a fundação técnica: FastAPI, PostgreSQL, SQLAlchemy assíncrono, Alembic, seed, Next.js e documentação arquitetural. Autenticação e regras do fluxo de compra ainda não foram implementadas.

## Arquitetura

O projeto é um monólito modular com frontend e backend implantáveis separadamente:

```text
Next.js -> FastAPI -> PostgreSQL
                 -> Ticketmaster API (fase posterior)
```

Detalhes estão em [docs/architecture.md](docs/architecture.md).

## Stack

- Frontend: Next.js, React, TypeScript e Tailwind CSS.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2 e Alembic.
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

## Migrations

Execute migrations a partir de `backend/`:

```powershell
alembic upgrade head
alembic downgrade -1
```

## Seed

O seed é idempotente e cria quatro usuários de desenvolvimento:

| Papel | E-mail | Senha local padrão |
|---|---|---|
| Organizador | `organizer@elite.local` | `DevOnly123!` |
| Cliente | `customer1@elite.local` | `DevOnly123!` |
| Cliente | `customer2@elite.local` | `DevOnly123!` |
| Portaria | `gate@elite.local` | `DevOnly123!` |

A senha pode ser alterada por `SEED_PASSWORD`. Essas credenciais existem somente para desenvolvimento e não devem ser usadas em produção.

## Testes

A suíte de regras de negócio será adicionada junto aos respectivos módulos. Nesta fase, valide o backend com `/health`, a migration com `alembic upgrade head` e o frontend com `npm run build`.

## Uso de IA

O uso de assistência por IA está descrito com transparência em [docs/ai-usage.md](docs/ai-usage.md).

## Trade-offs e limitações conhecidas

- O Compose inicial executa apenas o PostgreSQL; backend e frontend rodam localmente para agilizar o desenvolvimento.
- A modelagem prepara as regras do domínio, mas autenticação, catálogo, reservas, pagamentos, tickets e portaria serão implementados nas próximas fases.
- Expiração automática de reservas, mapas de assento, filas, cache e pagamentos reais estão fora do MVP inicial.

## Melhorias futuras

As próximas fases seguirão a ordem: autenticação e eventos; reservas; pagamentos e tickets; portaria e compartilhamento; testes e qualidade; entrega.

