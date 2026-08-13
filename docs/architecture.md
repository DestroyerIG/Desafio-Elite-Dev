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

A integração com Ticketmaster será feita pelo FastAPI. A chave externa nunca será exposta ao navegador, e eventos publicados serão copiados para o PostgreSQL para remover a dependência do catálogo durante a navegação pública.

## Backend

Os módulos de domínio seguem o fluxo `Router -> Service -> Repository -> PostgreSQL`:

- Router: protocolo HTTP, dependências, parâmetros e status codes.
- Service: autorização específica do domínio, transações e regras de negócio.
- Repository: consultas e persistência com SQLAlchemy.
- Schemas: contratos de entrada e saída validados pelo Pydantic.

O módulo de health já usa esse fluxo em versão mínima e executa `SELECT 1`, provando que a sessão assíncrona alcança o PostgreSQL.

## Frontend

O App Router organiza áreas pública, de cliente, de organizador e de portaria. A fundação da Fase 1 inclui apenas a página inicial e os diretórios compartilhados; as rotas de produto serão adicionadas com seus fluxos para evitar interfaces fictícias.

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

