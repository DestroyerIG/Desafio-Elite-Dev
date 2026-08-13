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

