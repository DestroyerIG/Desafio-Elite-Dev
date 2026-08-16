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

O App Router oferece página inicial, catálogo público, login, área do organizador, checkout protegido, "Minhas reservas", "Meus ingressos", ingresso público compartilhado e `/gate`. Uma reserva pendente pode ser retomada pelo identificador presente na URL. Após a aprovação, o checkout abre diretamente o primeiro ingresso e carrega seu QR autenticado. O compartilhamento apresenta o mesmo QR por um token público limitado. A portaria processa a câmera localmente com `jsQR`, mantém código manual como fallback e envia somente a credencial lida à API. TanStack Query controla cache e estados de requisição; Zod valida formulários.

## Persistência

O schema inicial contém:

- `users`: identidade e papel de acesso.
- `events`: cópia local de um evento externo e seu estoque.
- `reservations`: intenção de compra por quantidade e preço congelado.
- `payments`: histórico das tentativas de pagamento associadas à reserva.
- `tickets`: uma unidade de ingresso por linha.
- `ticket_shares`: compartilhamentos públicos por hash de token.
- `ticket_validations`: trilha de auditoria da portaria.

Constraints no PostgreSQL protegem unicidade, quantidades, preços e relações essenciais. A criação da reserva bloqueia a linha do evento com `SELECT FOR UPDATE`, valida o estoque, diminui a disponibilidade e insere a reserva na mesma transação. Cancelamento bloqueia evento e reserva nessa ordem antes de devolver estoque.

Cada tentativa de pagamento bloqueia a reserva e persiste seu resultado. Uma recusa mantém a reserva pendente e não cria tickets. Quando aprovada, a mesma transação altera o status, persiste o pagamento e cria exatamente uma linha de ticket por unidade. Cada ticket recebe código público e hash de um JWT assinado com segredo independente. O token é recriado ao gerar o PNG do QR e nunca é persistido em texto puro.

O compartilhamento persiste apenas o hash SHA-256 de um token aleatório e oferece detalhe e QR públicos somente leitura. Na portaria, QR e código manual convergem para o mesmo serviço. O ticket é localizado com `SELECT FOR UPDATE`; a decisão, a mudança para `USED` e a linha de auditoria em `ticket_validations` são confirmadas na mesma transação.
