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

Na Fase 2, essa separação foi aplicada aos módulos `auth`, `catalog` e `events`. O `TicketmasterClient` fica na camada de integrações e o catálogo expõe apenas um DTO controlado pela aplicação.

O JWT identifica usuário e papel, mas a autorização não confia apenas no token: a dependency carrega o usuário atual no PostgreSQL e os services verificam a propriedade do evento antes de editar ou excluir.

## Frontend

O App Router já oferece página inicial, listagem e detalhe públicos, login e área do organizador. TanStack Query controla cache, carregamento, erros e invalidação após mutações; Zod valida os formulários antes de chamar a API. Áreas de cliente e portaria serão adicionadas junto aos fluxos correspondentes.

## Persistência

O schema inicial contém:

- `users`: identidade e papel de acesso.
- `events`: cópia local de um evento externo e seu estoque.
- `reservations`: intenção de compra por quantidade e preço congelado.
- `payments`: resultado do pagamento associado à reserva.
- `tickets`: uma unidade de ingresso por linha.
- `ticket_shares`: compartilhamentos públicos por hash de token.
- `ticket_validations`: trilha de auditoria da portaria.

Constraints no PostgreSQL protegem unicidade, quantidades, preços e relações essenciais. Nas fases seguintes, locks pessimistas protegerão estoque e uso único do ingresso em cenários concorrentes.
