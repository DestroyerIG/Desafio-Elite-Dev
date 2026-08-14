# Decisões técnicas

## Monólito modular

O domínio e o prazo não justificam microserviços. Separar módulos no FastAPI preserva limites claros sem introduzir rede interna, consistência distribuída ou custo operacional adicional.

## SQLAlchemy assíncrono

O backend usa `AsyncSession` e `asyncpg`. Isso mantém o ciclo HTTP não bloqueante e oferece controle explícito das transações que serão usadas em reservas e validações. Uma sessão é aberta por requisição e sempre fechada pela dependency.

## Migrations com Alembic

O banco não é criado automaticamente na inicialização. O Alembic versiona mudanças de schema e torna ambientes locais, testes e deploys reproduzíveis. Sem migrations, alterações de models poderiam deixar bancos em estados incompatíveis.

## Integridade também no banco

Checks garantem capacidade positiva, estoque entre zero e capacidade, quantidade de reserva positiva e valores monetários não negativos. Uniques protegem e-mail, código público, hash de compartilhamento e a relação 1:1 entre pagamento e reserva. Validação na aplicação continuará necessária para mensagens de erro úteis.

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
