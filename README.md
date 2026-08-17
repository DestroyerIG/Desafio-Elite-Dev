# Elite Events

## Visão geral

Plataforma full-stack de eventos e ingressos do Desafio Elite Dev 2026. O MVP cobre criação e importação de eventos, reserva com proteção contra overselling, pagamento simulado, emissão de ingressos individuais, QR assinado, compartilhamento e validação na portaria.

O repositório contém o fluxo principal completo: autenticação JWT com RBAC, catálogo externo da Ticketmaster, publicação local de eventos, busca e filtros na agenda pública, reservas protegidas contra overselling, mapas de assentos em tempo real, pagamento e reembolso simulados, ingressos individuais com QR assinado, compartilhamento público somente leitura e validação transacional na portaria. O Next.js oferece experiências específicas para público, cliente, organizador e portaria.

## Arquitetura

O projeto é um monólito modular com frontend e backend implantáveis separadamente:

```text
Next.js -> FastAPI -> PostgreSQL
                 -> Ticketmaster Discovery API
        <- WebSocket + PostgreSQL LISTEN/NOTIFY
```

Detalhes estão em [docs/architecture.md](docs/architecture.md).

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, TanStack Query, Zod e jsQR.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2, Alembic, HTTPX, PyJWT, qrcode e Argon2.
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

No backend, substitua `JWT_SECRET` e `TICKET_SECRET` por chaves aleatórias fortes e independentes e informe `TICKETMASTER_API_KEY` para habilitar a busca no catálogo. A chave da Ticketmaster nunca é enviada ao frontend. Em produção, a aplicação rejeita os segredos documentados de desenvolvimento.

## Endpoints implementados

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/me
GET    /api/v1/catalog/events?q=
GET    /api/v1/events?q=&date_from=&date_to=&available_only=
GET    /api/v1/events/{id}
POST   /api/v1/events
PATCH  /api/v1/events/{id}
DELETE /api/v1/events/{id}
GET    /api/v1/organizer/events
POST   /api/v1/organizer/events
GET    /api/v1/events/{id}/seat-map
WS     /api/v1/events/{id}/seat-map/stream
GET    /api/v1/organizer/events/{id}/seat-map
PUT    /api/v1/organizer/events/{id}/seat-map
DELETE /api/v1/organizer/events/{id}/seat-map
POST   /api/v1/events/{id}/seat-holds
POST   /api/v1/events/{id}/reservations
GET    /api/v1/me/reservations
GET    /api/v1/reservations/{id}
POST   /api/v1/reservations/{id}/cancel
POST   /api/v1/reservations/{id}/payments
POST   /api/v1/reservations/{id}/refunds
GET    /api/v1/me/tickets
GET    /api/v1/tickets/{id}
GET    /api/v1/tickets/{id}/qr
POST   /api/v1/tickets/{id}/share
GET    /api/v1/shared-tickets/{token}
GET    /api/v1/shared-tickets/{token}/qr
POST   /api/v1/gate/validate
```

Cadastro público sempre cria um `CUSTOMER`. Pesquisa no catálogo e mutações de eventos exigem um JWT de `ORGANIZER`; a listagem e o detalhe de eventos publicados são públicos. O organizador pode importar um evento da Ticketmaster ou criar um evento próprio com imagem JPEG, PNG ou WebP de até 5 MB. As imagens ficam em `backend/uploads`, são servidas por `/uploads` e o Dockerfile reserva `/app/uploads` como volume persistente. Na listagem, `q` pesquisa título, nome e endereço do local sem diferenciar maiúsculas de minúsculas; `date_from` e `date_to` aceitam instantes ISO 8601 com fuso; `available_only=true` remove eventos esgotados. A página `/events` oferece esses filtros e mantém a seleção na URL. Somente o `CUSTOMER` proprietário lista, acessa, cancela ou paga suas reservas e consulta ou compartilha seus ingressos. Apenas usuários `GATE` validam entradas.

O gateway de pagamento é simulado. O cartão de teste `4242 4242 4242 4242` é aprovado; números terminados em `0000` são recusados. O número é usado somente durante a chamada e não é persistido. Cada tentativa fica registrada. Depois de uma recusa, a reserva continua `PENDING` e pode ser retomada em "Minhas reservas" com outro cartão. O estoque permanece reservado até o pagamento ou cancelamento manual, e ingressos são emitidos somente após a aprovação. A resposta aprovada informa os IDs emitidos e o checkout abre diretamente o primeiro ingresso com seu QR; os demais permanecem em "Meus ingressos".

Eventos podem operar por quantidade (`GENERAL_ADMISSION`) ou com lugares marcados (`ASSIGNED`). O organizador gera um mapa retangular por setores, e a capacidade do mapa precisa coincidir exatamente com a capacidade publicada. Reservas gerais canceladas, expiradas ou reembolsadas não impedem a primeira configuração quando todo o estoque já foi restaurado; depois da primeira reserva de assento, a estrutura fica bloqueada. O cliente seleciona até 10 assentos; o backend bloqueia evento e lugares em ordem estável e cria o hold inteiro ou retorna `409`, sem seleção parcial. Holds duram 10 minutos, são expirados por um processo seguro para múltiplas instâncias e também verificados no acesso ao mapa e no pagamento. Pagamento transforma `HELD` em `SOLD`; cancelamento, expiração e reembolso devolvem os lugares uma única vez.

Mudanças incrementam a versão do mapa e publicam `pg_notify` somente no commit. Cada instância FastAPI escuta o canal e retransmite um aviso mínimo aos navegadores por WebSocket; o cliente busca novamente o snapshot oficial. Reconexão exponencial e polling de 15 segundos recuperam mensagens perdidas sem usar Redis.

Reservas `PAID` podem receber reembolso integral em até 7 dias após o pagamento e com no mínimo 48 horas de antecedência do evento. Eventos `CANCELLED` dispensam esses prazos. Todos os ingressos precisam estar `ACTIVE`; qualquer check-in bloqueia a operação. O simulador aprova o reembolso imediatamente e, na mesma transação, registra `refunds`, altera reserva e ingressos para `REFUNDED`, revoga compartilhamentos e devolve a quantidade ao estoque uma única vez. A interface oferece a ação no checkout e em "Minhas reservas".

O proprietário pode gerar um link público para um ingresso. O token aleatório aparece somente na resposta de criação e o PostgreSQL recebe apenas seu SHA-256. O link permite consultar os dados e o QR, sem qualquer operação de alteração. Na rota `/gate`, a portaria escolhe o evento e usa câmera ou código manual. O backend bloqueia o ticket com `SELECT FOR UPDATE`, marca `USED` e registra toda tentativa como `VALID`, `INVALID`, `ALREADY_USED` ou `WRONG_EVENT`.

Para validar manualmente a Fase 5: entre como cliente, abra um ingresso pago e gere o link compartilhável; teste-o em uma janela anônima. Depois entre como `gate@example.com`, acesse `/gate`, selecione o evento e leia o QR ou informe o `public_code`. A primeira leitura correta deve liberar a entrada e a segunda deve informar que o ingresso já foi utilizado.

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

A suíte integrada possui um PostgreSQL próprio e um executor protegido:

```powershell
docker compose --profile test up -d --wait db_test
cd backend
python scripts/run_integration_tests.py
```

O executor recusa bancos cujo nome não contenha `test`, recria o schema, aplica migrations e seed e então executa os cenários concorrentes. A suíte comprova busca e filtros públicos, reserva concorrente sem overselling, disputa pelo mesmo assento com um único vencedor, expiração de hold, pagamento recusado sem ingresso, nova tentativa aprovada na mesma reserva, pagamento concorrente sem duplicação, reembolso concorrente idempotente, prazos de elegibilidade, devolução exata ao estoque e aos assentos, invalidação de QR e compartilhamento, bloqueio após check-in, emissão exata e validação concorrente sem dupla entrada. A matriz completa está em [docs/testing.md](docs/testing.md).

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
- O armazenamento de imagens usa o disco local no MVP. Em execução via contêiner, monte um volume persistente em `/app/uploads`; múltiplas instâncias exigirão armazenamento compartilhado, como S3 ou R2.
- O token JWT é mantido em `localStorage` neste MVP. Isso simplifica o cliente, mas exige disciplina contra XSS; uma evolução para produção pode usar cookie `HttpOnly` com proteção CSRF ou um BFF.
- Sem `TICKETMASTER_API_KEY`, o catálogo retorna um erro de configuração explícito; eventos locais publicados continuam disponíveis.
- Pagamento e reembolso são deliberadamente simulados. Todas as tentativas de pagamento e o reembolso integral ficam registrados, mas nenhum dado de cartão é persistido. Reembolso parcial e processamento assíncrono por webhook permanecem fora do MVP.
- O QR é gerado sob demanda a partir de um JWT assinado; somente seu hash é persistido. Rotação de `TICKET_SECRET` exige uma estratégia de reemissão, ainda fora do MVP.
- Links de compartilhamento não expiram e ainda não possuem revogação pela interface; o schema já reserva `expires_at` e `revoked_at` para essa evolução.
- O scanner processa imagens localmente com `jsQR`. A câmera depende de permissão do usuário e de contexto seguro (`HTTPS` ou `localhost`); o código manual permanece disponível como fallback.
- Reservas por quantidade permanecem `PENDING` até pagamento ou cancelamento manual. Somente holds de assentos marcados expiram automaticamente após 10 minutos.
- O mapa usa setores retangulares, preço único do evento e até 2.000 lugares. Editor visual livre, preços por setor, filas, cache externo e pagamentos reais permanecem fora do escopo atual.

## Melhorias futuras

As próximas fases seguirão a ordem: testes e qualidade; entrega.
