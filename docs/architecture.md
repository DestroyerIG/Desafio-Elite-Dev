# Arquitetura

## Visão geral

Elite Events adota um monólito modular. O backend concentra autenticação, autorização, regras de negócio, integração externa e persistência; o frontend consome apenas a API HTTP.

```text
┌────────────────┐       HTTP       ┌─────────────────────────┐
│ Next.js        │ ───── HTTP ─────> │ FastAPI                 │
│ React/TS       │ <── HTTP/WS ───── │ módulos de domínio      │
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

Essa separação foi aplicada aos módulos `auth`, `catalog`, `events`, `reservations`, `payments`, `seats` e `tickets`. O `TicketmasterClient` fica na camada de integrações e o catálogo expõe apenas um DTO controlado pela aplicação.

O JWT identifica usuário e papel, mas a autorização não confia apenas no token: a dependency carrega o usuário atual no PostgreSQL e os services verificam a propriedade do evento antes de editar ou excluir.

## Frontend

O App Router oferece página inicial, agenda pública, catálogo do organizador, login, área do organizador, checkout protegido, "Minhas reservas", "Meus ingressos", ingresso público compartilhado e `/gate`. Na agenda, texto, período e disponibilidade ficam serializados na URL; a API aplica os critérios diretamente no PostgreSQL e o TanStack Query separa o cache por combinação de filtros. Uma reserva pendente pode ser retomada pelo identificador presente na URL. Após a aprovação, o checkout abre diretamente o primeiro ingresso e carrega seu QR autenticado. Reservas pagas elegíveis podem ser reembolsadas no checkout ou em "Minhas reservas"; as consultas de eventos, reservas e ingressos são invalidadas juntas para refletir o novo estado. O compartilhamento apresenta o mesmo QR por um token público limitado. A portaria processa a câmera localmente com `jsQR`, mantém código manual como fallback e envia somente a credencial lida à API. TanStack Query controla cache e estados de requisição; Zod valida formulários.

## Persistência

O schema contém:

- `users`: identidade e papel de acesso.
- `events`: cópia local de um evento externo e seu estoque.
- `reservations`: intenção de compra por quantidade e preço congelado.
- `payments`: histórico das tentativas de pagamento associadas à reserva.
- `refunds`: registro único do reembolso integral associado à reserva e ao pagamento aprovado.
- `seat_maps` e `seat_sections`: estrutura retangular e versão pública do mapa.
- `event_seats`: estado atual de cada lugar e sua reserva ativa.
- `reservation_seats`: vínculo histórico, com liberação explícita do lugar.
- `tickets`: uma unidade de ingresso por linha.
- `ticket_shares`: compartilhamentos públicos por hash de token.
- `ticket_validations`: trilha de auditoria da portaria.

Constraints no PostgreSQL protegem unicidade, quantidades, preços e relações essenciais. A criação da reserva bloqueia a linha do evento com `SELECT FOR UPDATE`, valida o estoque, diminui a disponibilidade e insere a reserva na mesma transação. Cancelamento bloqueia evento e reserva nessa ordem antes de devolver estoque.

Cada tentativa de pagamento bloqueia a reserva e persiste seu resultado. Uma recusa mantém a reserva pendente e não cria tickets. Quando aprovada, a mesma transação altera o status, persiste o pagamento e cria exatamente uma linha de ticket por unidade. Cada ticket recebe código público e hash de um JWT assinado com segredo independente. O token é recriado ao gerar o PNG do QR e nunca é persistido em texto puro.

Em eventos com assento marcado, a seleção bloqueia primeiro o evento e depois os IDs dos lugares em ordem determinística. A operação é integral: se um lugar não estiver `AVAILABLE`, nenhum hold é criado. O vínculo ativo e um índice parcial único impedem duas reservas simultâneas para o mesmo assento. Holds vencidos são processados em lotes por evento, sempre sob locks, e liberam estoque apenas uma vez.

Pagamento, cancelamento e reembolso estendem as mesmas transações para alterar lugares entre `HELD`, `SOLD` e `AVAILABLE`. O ingresso mantém `seat_id` mesmo depois de um reembolso para preservar o histórico, enquanto `event_seats.active_reservation_id` aponta somente para a ocupação atual.

O reembolso bloqueia evento, reserva e ingressos nessa ordem. Depois de validar propriedade, prazo, antecedência e ausência de check-in, o simulador aprova a devolução. Registro financeiro, estados `REFUNDED`, revogação dos compartilhamentos e reposição do estoque são confirmados na mesma transação. A unicidade de `refunds.reservation_id`, combinada aos locks, impede reembolso ou devolução duplicados.

O compartilhamento persiste apenas o hash SHA-256 de um token aleatório e oferece detalhe e QR públicos somente leitura. Na portaria, QR e código manual convergem para o mesmo serviço. O ticket é localizado com `SELECT FOR UPDATE`; a decisão, a mudança para `USED` e a linha de auditoria em `ticket_validations` são confirmadas na mesma transação.

Cada mudança do mapa incrementa `seat_maps.version` e executa `pg_notify` dentro da transação; o PostgreSQL só entrega a mensagem após o commit. Um listener `asyncpg` por instância distribui a versão para conexões WebSocket locais. O payload não contém dados do comprador. Ao receber a versão, o frontend invalida o cache e busca um snapshot completo; polling periódico mantém consistência se a conexão cair.
