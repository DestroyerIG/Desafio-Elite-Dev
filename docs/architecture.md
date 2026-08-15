# Arquitetura

## Visão geral

Elite Events adota um monólito modular. O backend concentra autenticação, autorização, regras de negócio, integração externa e persistência; o frontend consome apenas a API HTTP.

```text
┌────────────────┐       HTTP       ┌─────────────────────────┐
│ Next.js        │ ────────────────> │ FastAPI                 │
│ React/TS       │ <──────────────── │ módulos de domínio      │
└────────────────┘                   └────────────┬────────────┘
                                                 │ SQLAlchemy
                                                 v
                                    ┌─────────────────────────┐
                                    │ PostgreSQL              │
                                    └─────────────────────────┘
```

A integração com Ticketmaster é feita pelo FastAPI. A chave externa nunca é exposta ao navegador, e eventos publicados são copiados para o PostgreSQL para remover a dependência do catálogo durante a navegação pública.

## Backend

Os módulos de domínio seguem o fluxo `Router -> Service -> Repository -> PostgreSQL`:

- Router: protocolo HTTP, dependências, parâmetros e status codes.
- Service: autorização específica do domínio, transações e regras de negócio.
- Repository: consultas e persistência com SQLAlchemy.
- Schemas: contratos de entrada e saída validados pelo Pydantic.

Essa separação foi aplicada aos módulos `auth`, `catalog`, `events`, `reservations`, `payments` e `tickets`. O `TicketmasterClient` fica na camada de integrações e o catálogo expõe apenas um DTO controlado pela aplicação.

O JWT identifica usuário e papel, mas a autorização não confia apenas no token: a dependency carrega o usuário atual no PostgreSQL e os services verificam a propriedade do evento antes de editar ou excluir.

## Frontend

O App Router já oferece página inicial, listagem e detalhe públicos, login, área do organizador, checkout protegido e "Meus ingressos". TanStack Query controla cache, carregamento, erros, QR autenticado em `Blob` e invalidação após mutações; Zod valida os formulários antes de chamar a API. A área de portaria será adicionada junto ao fluxo correspondente.

## Persistência

O schema inicial contém:

- `users`: identidade e papel de acesso.
- `events`: cópia local de um evento externo e seu estoque.
- `reservations`: intenção de compra por quantidade e preço congelado.
- `payments`: resultado do pagamento associado à reserva.
- `tickets`: uma unidade de ingresso por linha.
- `ticket_shares`: compartilhamentos públicos por hash de token.
- `ticket_validations`: trilha de auditoria da portaria.

Constraints no PostgreSQL protegem unicidade, quantidades, preços e relações essenciais. A criação da reserva bloqueia a linha do evento com `SELECT FOR UPDATE`, valida o estoque, diminui a disponibilidade e insere a reserva na mesma transação. Cancelamento bloqueia evento e reserva nessa ordem antes de devolver estoque.

O pagamento bloqueia a reserva e, quando aprovado, altera seu status, persiste o pagamento e cria exatamente uma linha de ticket por unidade na mesma transação. Cada ticket recebe código público e hash de um JWT assinado com segredo independente. O token é recriado somente para o proprietário ao gerar o PNG do QR e nunca é persistido em texto puro. Em uma fase seguinte, o mesmo princípio transacional protegerá o uso único do ingresso na portaria.
