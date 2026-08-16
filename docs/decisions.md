# Decisões técnicas

## Monólito modular

O domínio e o prazo não justificam microserviços. Separar módulos no FastAPI preserva limites claros sem introduzir rede interna, consistência distribuída ou custo operacional adicional.

## SQLAlchemy assíncrono

O backend usa `AsyncSession` e `asyncpg`. Isso mantém o ciclo HTTP não bloqueante e oferece controle explícito das transações que serão usadas em reservas e validações. Uma sessão é aberta por requisição e sempre fechada pela dependency.

## Migrations com Alembic

O banco não é criado automaticamente na inicialização. O Alembic versiona mudanças de schema e torna ambientes locais, testes e deploys reproduzíveis. Sem migrations, alterações de models poderiam deixar bancos em estados incompatíveis.

## Integridade também no banco

Checks garantem capacidade positiva, estoque entre zero e capacidade, quantidade de reserva positiva e valores monetários não negativos. Uniques protegem e-mail, código público e hash de compartilhamento. Pagamentos usam um índice não único por reserva para preservar o histórico de tentativas. Validação na aplicação continuará necessária para mensagens de erro úteis.

## Dinheiro com Decimal

Preços são `NUMERIC(10, 2)`, não ponto flutuante. Isso evita erros binários de arredondamento em totais e pagamentos.

## Tickets individuais

Uma reserva de quantidade N produzirá N linhas em `tickets`. Compartilhamento, QR, estado de uso e auditoria permanecem independentes por ingresso.

## Compose inicialmente só para PostgreSQL

Frontend e backend rodam no host durante o desenvolvimento, reduzindo o ciclo de feedback. O banco permanece reproduzível e isolado no Compose; o backend já possui Dockerfile para ambientes que precisem de containerização.

## CORS explícito

O backend aceita por padrão somente `http://localhost:3000`. A origem é configurável por ambiente; não é usado wildcard com credenciais.

## Segredos fora do Git

Somente exemplos de desenvolvimento são versionados. `.env`, JWT secret, ticket secret, senha de banco de produção e chave Ticketmaster ficam fora do repositório.

## JWT curto e autorização no banco

O token contém apenas `sub`, `role`, `iat` e `exp` e é assinado com HS256. A cada rota protegida, o backend valida assinatura e expiração, carrega o usuário e confirma que o papel do token ainda coincide com o banco. Isso permite revogar acesso removendo ou alterando o usuário sem depender apenas de uma afirmação antiga no JWT.

Senhas usam Argon2. Cadastro público nunca aceita um papel informado pelo cliente e sempre cria `CUSTOMER`, impedindo autoelevação para `ORGANIZER` ou `GATE`.

## Ticketmaster somente pelo backend

O navegador consulta o catálogo por meio do FastAPI. O cliente HTTP adiciona a API key apenas no servidor, aplica timeout e traduz falhas externas para erros estáveis da aplicação. Logs detalhados de HTTPX foram reduzidos para evitar que a query string com `apikey` apareça nos logs.

## Evento externo copiado para o PostgreSQL

Na publicação, o backend busca o evento novamente pelo identificador externo e grava os campos normalizados localmente. A página pública lê apenas o PostgreSQL. Assim, indisponibilidade, mudança ou remoção no catálogo não quebra um evento já publicado.

## Token no frontend

O MVP guarda o JWT no `localStorage` e o envia como Bearer token. A decisão mantém o fluxo separado entre Next.js e FastAPI simples nesta etapa, mas aumenta o impacto potencial de XSS. Uma implantação com requisitos de segurança mais altos deve avaliar cookie `HttpOnly`, proteção CSRF e uma camada BFF.

## Reserva com `SELECT FOR UPDATE`

A criação da reserva lê o evento publicado com lock pessimista. Enquanto a transação valida e reduz `available_tickets`, outra reserva para o mesmo evento espera. Quando prossegue, a segunda transação enxerga o estoque já confirmado e falha com `409` se não houver quantidade suficiente. Uma verificação somente no frontend ou um `SELECT` sem lock permitiria que duas requisições consumissem o mesmo último ingresso.

Edição e exclusão pelo organizador usam o mesmo lock da linha do evento. Isso evita que uma alteração concorrente de capacidade sobrescreva a redução realizada por uma reserva.

## Cancelamento idempotente e ordem de locks

Cancelamento bloqueia primeiro o evento e depois a reserva. Manter uma ordem estável reduz o risco de deadlock com outros fluxos. A releitura bloqueada força `populate_existing`, pois uma instância previamente carregada no identity map do SQLAlchemy poderia conservar um status antigo após esperar pelo lock.

Cancelar novamente uma reserva já `CANCELLED` não devolve estoque outra vez. O preço unitário e o total permanecem congelados na reserva para que mudanças futuras no preço do evento não alterem a intenção de compra existente.

## Sem expiração automática nesta fase

`expires_at` permanece nulo. Expirar reservas exigiria um processo confiável para localizar pendências e devolver estoque exatamente uma vez. O roadmap orienta adiar essa automação até o MVP principal estar completo; nesta fase, a liberação ocorre apenas por cancelamento explícito.

## Gateway de pagamento substituível

O service depende do contrato `PaymentGateway`; a Fase 4 fornece apenas `FakePaymentGateway`. Cartões de teste terminados em `0000` são recusados e os demais números válidos são aprovados. O número completo existe apenas no objeto de entrada durante a autorização: não há coluna, log ou resposta que o persista.

## Pagamento e emissão na mesma transação

O pagamento bloqueia a reserva com `SELECT FOR UPDATE`. Aprovação, mudança para `PAID` e criação de N tickets são confirmadas juntas; qualquer erro reverte tudo. Isso impede uma reserva paga sem todos os ingressos ou ingressos sem pagamento aprovado. Depois da aprovação, o status `PAID`, combinado ao lock, torna repetições idempotentes e evita novas cobranças ou emissão duplicada.

O schema representa cada autorização como uma tentativa separada. Uma recusa é registrada, mantém a reserva `PENDING` e não cria ingressos; o cliente pode informar outro cartão e tentar novamente na mesma reserva. A migration `20260816_0002` removeu a unicidade de `payments.reservation_id` e criou um índice comum para suportar esse histórico sem armazenar números de cartão.

## QR assinado e hash persistido

O conteúdo do QR é um JWT HS256 contendo somente `ticket_id`, `event_id` e `type=ticket`, assinado por `TICKET_SECRET`, separado do segredo de autenticação. O banco guarda apenas SHA-256 do token. Ao solicitar o PNG autenticado, o backend recria o token determinístico e compara seu hash em tempo constante antes de gerar a imagem.

UUID puro permitiria fabricar códigos visualmente plausíveis; a assinatura comprova origem e integridade. O estado do ticket continua no PostgreSQL, portanto a assinatura não substitui a verificação transacional que será implementada na portaria. Como trade-off, rotacionar o segredo atual invalida a regeneração dos QRs existentes sem uma estratégia de versionamento ou reemissão.
