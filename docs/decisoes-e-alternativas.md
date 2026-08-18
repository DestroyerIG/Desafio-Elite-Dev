# Decisões e alternativas

Este documento registra as decisões que tomei, o que descartei em cada uma e o que a escolha me custa. O [docs/decisions.md](decisions.md) descreve **o que** o sistema faz; aqui explico **por que isso e não a alternativa**.

Escrevi o campo "o que isso me custa" em todas as entradas de propósito. Toda decisão de arquitetura tem um preço, e quem só sabe elogiar a própria escolha não a entendeu por completo.

---

## Concorrência: o núcleo do desafio

### Reserva com `SELECT FOR UPDATE`

**A decisão.** A criação da reserva abre uma transação, lê a linha do evento com lock pessimista (`SELECT ... FOR UPDATE`), confere `available_tickets >= quantity`, decrementa o estoque e grava a reserva. Só então faz commit.

**O que descartei.**

*Validar apenas no frontend.* Descartado de imediato: o navegador trabalha com um retrato do estoque de segundos atrás. Tenho um print disso em [erros.md](erros.md#estoque-insuficiente--a-prova-de-que-o-frontend-não-basta) — a página exibe 95 disponíveis, o cliente pede 95, e o servidor recusa porque outro comprou nesse intervalo. A validação do cliente é conveniência, nunca garantia.

*`SELECT` sem lock, seguido de `UPDATE`.* É a armadilha mais comum. Entre a leitura e a escrita existe uma janela em que outra transação lê o mesmo valor. Duas requisições enxergam "resta 1" e ambas vendem.

*`UPDATE` condicional atômico* (`UPDATE events SET available_tickets = available_tickets - :n WHERE id = :id AND available_tickets >= :n`). Esta é a alternativa séria, e é mais rápida: uma ida ao banco, sem lock explícito, correta em qualquer nível de isolamento. Descartei por dois motivos. Primeiro, a reserva não é uma operação isolada: no modo com assentos marcados eu preciso travar o evento **e** as linhas de `seats` na mesma transação, com ordem estável, e o lock explícito deixa essa ordem legível no código. Segundo, o `UPDATE` condicional comunica a falha pela contagem de linhas afetadas, o que espalha a regra de negócio entre SQL e Python; com o lock, a checagem fica inteira no service, junto do erro que o usuário vai ver. Em um sistema só de quantidade, eu teria escolhido o `UPDATE` condicional.

*Lock otimista por versão.* Bom quando conflitos são raros — o que é o oposto de venda de ingresso, em que todo mundo chega junto no mesmo instante. Sob disputa real, viraria uma sequência de retentativas e mensagens de conflito.

*`SERIALIZABLE`.* Resolveria de forma genérica, mas transfere o problema para o cliente: sob concorrência o PostgreSQL aborta transações com erro de serialização, e eu precisaria de laço de retentativa em toda a aplicação. Mais complexidade para o mesmo resultado.

*Lock distribuído em Redis.* Introduziria um componente novo, com sua própria disponibilidade, para proteger um dado que já mora no PostgreSQL. O banco já sabe fazer isso e o lock morre junto com a transação — sem lock órfão se o processo cair.

**O que isso me custa.** Locks pessimistas serializam as reservas do **mesmo** evento: com um lote muito concorrido, as requisições formam fila. É aceitável porque a seção crítica é curta (uma leitura, uma comparação, dois `UPDATE`) e porque eventos diferentes não se bloqueiam. Se um único evento passasse a receber milhares de compras por segundo, eu migraria para o `UPDATE` condicional e mediria de novo.

### Como o overselling é barrado, em camadas

Nenhuma camada isolada resolve; a garantia vem da combinação.

| Camada | Papel | Sozinha basta? |
|---|---|---|
| `max` no input de quantidade | Evita erro óbvio antes da viagem | Não — trabalha com dado defasado |
| Validação Pydantic | Rejeita quantidade ≤ 0 ou não inteira | Não — não conhece o estoque |
| `SELECT FOR UPDATE` + checagem | **A garantia real** | Sim, para este fluxo |
| `CHECK (available_tickets >= 0)` | Rede de segurança do schema | Não — só impede o absurdo final |
| Índice único parcial em `reservation_seats` | Exclusividade do assento | Sim, para assento marcado |

O `CHECK` merece nota: ele não previne overselling, ele **prova** que o lock funciona. Se algum caminho novo esquecesse a transação, o banco recusaria a escrita em vez de gravar estoque negativo silenciosamente. É um detector de bug, não uma trava de negócio.

E o teste que sustenta tudo isso não é unitário: `test_concurrent_reservations_do_not_oversell` dispara reservas simultâneas contra um PostgreSQL real e verifica que a soma vendida nunca ultrapassa a capacidade. Concorrência com banco mockado não prova nada.

### Dupla validação do mesmo QR

**A decisão.** A portaria roda a mesma sequência da reserva: transação, `SELECT FOR UPDATE` na linha do ticket, e só então a verificação de evento e status. A primeira transação marca `USED` e faz commit; a segunda espera o lock, relê o estado já confirmado e responde `ALREADY_USED`.

**O que descartei.**

*Ler o status sem lock.* Duas catracas lendo o mesmo QR no mesmo segundo leriam ambas `ACTIVE` e liberariam duas entradas. É o mesmo bug do overselling em outra roupagem.

*Confiar na assinatura do QR.* A assinatura prova **origem e integridade**, não que o ingresso não foi usado. Estado é sempre do banco. Um QR legítimo fotografado e reenviado continua legítimo — o que o barra é o `USED`.

*Idempotência só por constraint única em `ticket_validations`.* Bloquearia o segundo registro, mas com um erro de integridade, não com uma resposta de negócio. A portaria precisa distinguir "já utilizado" de "falhou", e um operador com fila na frente precisa de uma resposta clara, não de um 500.

*Expiração curta no token do QR.* Não resolve: o ataque não é usar um QR velho, é usar o mesmo QR duas vezes dentro da janela válida.

**A ordem das checagens é intencional.** Evento é verificado **antes** do status de uso. Assim um ingresso apresentado no portão errado responde `WRONG_EVENT` sem ser consumido — a pessoa ainda consegue entrar no evento certo. Invertida, a ordem queimaria o ingresso no portão errado.

**O que isso me custa.** Cada validação é uma transação com lock. Numa entrada com muitas catracas simultâneas, leituras do mesmo ticket serializam — que é exatamente o que se quer — mas a operação toda depende do banco estar disponível. Sem conexão, não há validação offline. Numa portaria real com internet instável, isso exigiria fila local com reconciliação, e aí a garantia de unicidade mudaria de natureza.

---

## Persistência

### SQLAlchemy 2 assíncrono com asyncpg

**A decisão.** `AsyncSession` sobre asyncpg, uma sessão por requisição, fornecida por dependency e sempre fechada por ela.

**O que descartei.**

*SQLAlchemy síncrono com o threadpool do FastAPI.* Funcionaria, e para este volume a diferença de desempenho seria imperceptível. Descartei pela coerência: o resto do backend é async (HTTPX para a Ticketmaster, WebSocket da portaria, `LISTEN/NOTIFY` dos assentos). Misturar sessão bloqueante com um event loop é a origem de travamentos difíceis de diagnosticar, e a fronteira entre os dois mundos precisaria ser respeitada em todo endpoint novo.

*asyncpg puro, com SQL escrito à mão.* Mais rápido e mais explícito. Descartei porque eu perderia o Alembic com autogeneração, o mapeamento de modelos e a checagem de tipos sobre as entidades — e ganharia SQL manual em dezenas de consultas. O gargalo deste sistema é lock de linha, não overhead de ORM.

*Django ORM.* Traria admin e migrations maduras de graça, mas o suporte async ainda é parcial justamente onde eu preciso dele — `select_for_update` em contexto assíncrono — e traria o framework inteiro para um projeto que é API pura.

**O que isso me custa.** O ecossistema async tem menos exemplos e mais armadilhas. Duas me custaram tempo de verdade: reutilizar conexão entre event loops diferentes nos testes, e o *identity map* devolvendo um objeto com estado anterior depois de esperar por um lock — resolvido com `populate_existing=True` na releitura travada. São bugs que a versão síncrona não teria.

### PostgreSQL

Escolhido porque as duas regras críticas do desafio — não vender além do estoque e não validar o mesmo ingresso duas vezes — são problemas de **consistência sob concorrência**. Transações, `FOR UPDATE`, constraints e índices parciais resolvem isso no lugar certo.

Descartei bancos de documentos: sem transação multi-documento com locking previsível, eu teria que reimplementar consistência na aplicação, que é exatamente o erro que este projeto evita.

`NUMERIC(10,2)` para dinheiro, nunca ponto flutuante — `0.1 + 0.2` não fecha em binário, e valores de ingresso somam.

---

## Tempo real

### `LISTEN/NOTIFY` do PostgreSQL, não Redis

**A decisão.** O mapa de assentos atualiza em tempo real assim: o PostgreSQL continua sendo a fonte da verdade; ao confirmar mudança, a transação emite `NOTIFY` com `event_id` e a versão do mapa; cada instância do FastAPI mantém um `LISTEN` e repassa o aviso por WebSocket; o navegador então **busca um snapshot novo** pela API.

O ponto central é que a notificação carrega apenas "mudou, versão N" — nunca o estado em si.

**O que descartei.**

*Redis pub/sub.* É a resposta padrão, e seria a certa em outra escala. Descartei porque aqui ele adicionaria um serviço a ser provisionado, monitorado e mantido no ar para transportar um aviso que o banco — que já é dependência obrigatória e já está na transação — sabe transportar. Num desafio de sete dias, cada componente novo é risco de deploy sem contrapartida de valor.

Há um detalhe que pesou mais que a simplicidade: com Redis, a publicação acontece **fora** da transação do PostgreSQL. Ou publico antes do commit, e posso anunciar uma mudança que ainda pode ser revertida, ou publico depois, e posso perder o aviso se o processo cair no intervalo. Com `NOTIFY` emitido dentro da transação, a entrega segue o destino dela: rollback não notifica.

*Polling puro.* Simples e robusto, mas escolher assento com atraso de segundos é uma experiência ruim — dois clientes disputam o mesmo lugar sem perceber.

*Fila durável (RabbitMQ, Kafka).* Sobra para o problema. Não preciso de histórico, replay nem garantia de entrega: se um aviso se perde, o cliente busca o snapshot na próxima oportunidade e converge.

**Por que isso funciona com várias instâncias.** Cada instância do FastAPI abre seu próprio `LISTEN`; o PostgreSQL entrega a todas. Não há estado em memória compartilhado entre processos — o estado está no banco, e a notificação é só um empurrão.

**O que isso me custa.** `NOTIFY` **não é durável**. Se a conexão de escuta cair, os avisos daquele intervalo se perdem para sempre — não há replay. Aceitei isso porque o aviso não carrega dado: assumo que ele pode sumir e trato a perda com reconexão em backoff mais polling de 15 segundos como rede de segurança. O modelo de versão fecha o ciclo: o cliente compara a versão recebida com a que possui e descarta avisos fora de ordem. Também existe um limite prático — cada instância consome uma conexão dedicada ao `LISTEN`, e o payload do `NOTIFY` é limitado a 8 KB, motivo adicional para transportar só o ponteiro.

---

## Segurança dos ingressos

### QR com JWT assinado e apenas o hash persistido

**A decisão.** O QR carrega um JWT HS256 com `ticket_id`, `event_id` e `type`, assinado com `TICKET_SECRET` — segredo separado do de autenticação. O banco guarda somente o SHA-256 do token. Ao gerar a imagem, o backend recria o token determinístico e compara os hashes em tempo constante.

**O que descartei.**

*UUID puro no QR.* Um identificador opaco parece seguro, mas não prova nada: qualquer pessoa pode gerar um UUID e apresentá-lo. A verificação seria só "existe no banco?" — o que transforma o QR num identificador adivinhável, sem autenticidade.

*Guardar o token completo no banco.* Quem lesse a tabela teria ingressos utilizáveis em mãos. Guardando o hash, um vazamento de leitura não produz QR válido.

*Segredo único para JWT de sessão e para ingressos.* Separei porque os ciclos de vida diferem: girar o segredo de sessão é barato — todo mundo faz login de novo. Girar o de ingresso invalidaria QRs já emitidos e distribuídos.

**O que isso me custa.** Rotacionar `TICKET_SECRET` hoje quebra a regeneração de todos os QRs existentes, porque não há versionamento de chave no payload. Uma evolução guardaria um `kid` e manteria a chave anterior aceita durante a transição. Para o MVP, o custo é conhecido e o benefício de não persistir o token compensa.

### Compartilhamento por token opaco

Cada solicitação gera 32 bytes aleatórios; o token bruto é devolvido **uma única vez** e o banco guarda apenas o SHA-256. O endpoint público expõe evento, código, status e QR daquele ingresso — sem IDs internos e sem qualquer mutação.

Descartei usar o `ticket_id` na URL: expor o identificador interno permitiria enumeração e confundiria "conhecer o link" com "ter direito ao ingresso". Como o token é parte da rota, um filtro substitui esse segmento por `[REDACTED]` no log de acesso — senão o segredo vazaria para o lugar mais banal possível.

Custo assumido: sem expiração nem revogação pela interface no MVP. O schema já reserva `expires_at` e `revoked_at`; a lacuna é de produto, não de modelagem.

---

## Domínio e modelagem

### N ingressos individuais, não um contador na reserva

Comprar 3 ingressos gera 3 linhas em `tickets`. Descartei guardar `quantity` na reserva e emitir um QR só, porque cada ingresso tem ciclo de vida próprio: entra sozinho na portaria, é compartilhado sozinho, é auditado sozinho. Com contador, "2 das 3 pessoas já entraram" viraria um campo mutável com regra de negócio em cima — e a validação transacional teria que travar a reserva inteira em vez da linha de um ingresso.

Custo: mais linhas e um `INSERT` por unidade. Irrelevante nesta escala.

### Ingresso por quantidade primeiro, assento marcado depois

O enunciado permitia escolher. Fui por quantidade para fechar o fluxo completo — publicar, reservar, pagar, emitir, compartilhar, validar — antes de abrir qualquer frente nova. Assentos marcados vieram depois, como modo adicional (`GENERAL_ADMISSION` ou `ASSIGNED`), sem quebrar o que já funcionava.

A ordem importa mais que o recurso: um mapa de assentos bonito sobre um fluxo incompleto não demonstra nada.

### Gateway de pagamento atrás de um contrato

O service depende do protocolo `PaymentGateway`; a implementação atual é `FakePaymentGateway` (cartão terminado em `0000` recusa). Pagamento e emissão acontecem na **mesma transação**: aprovação, mudança para `PAID` e criação dos N tickets confirmam juntas, ou nada acontece. Não existe reserva paga sem ingresso, nem ingresso sem pagamento aprovado.

Cada tentativa é uma linha em `payments` — a migration `20260816_0002` removeu a unicidade por reserva justamente para isso. Uma recusa mantém a reserva `PENDING` e o estoque separado; o cliente troca o cartão e tenta de novo, sem recomeçar a compra.

O número do cartão existe apenas no objeto de entrada durante a autorização: não há coluna, log ou resposta que o persista.

Custo assumido: o simulador conclui tudo de forma síncrona. Um provedor real exigiria idempotency key, webhook assinado e reconciliação antes de liberar estoque — e o texto de recusa dele precisaria de tradução antes de virar mensagem de usuário, ponto que já está isolado no service.

---

## Arquitetura e stack

### Monólito modular

Módulos com fronteira clara (`router` → `service` → `repository`), num único processo. Descartei microserviços: dividiria por rede um domínio cujas regras mais importantes são transações que atravessam evento, reserva, pagamento e ingresso. Com serviços separados, o `SELECT FOR UPDATE` viraria saga com compensação — muito mais complexidade para resolver um problema que eu não tenho.

Custo: nada impede, no código, que um módulo importe o repositório de outro. A disciplina é convenção, não barreira física.

### FastAPI

Validação com Pydantic nas bordas, OpenAPI automático e async nativo — que a integração externa e o tempo real exigiam. Descartei Django (framework completo demais para uma API pura, async parcial onde eu precisava) e Node/Express (perderia a tipagem de entrada e saída que o Pydantic dá sem esforço).

### JWT no `localStorage`

A decisão mais discutível do projeto, e assumo como tal. Mantém o Next.js e o FastAPI desacoplados, sem sessão compartilhada nem proxy — e o custo é exposição a XSS: script injetado lê o token.

Descartei cookie `HttpOnly` **para o MVP** porque exigiria proteção CSRF e domínio comum ou CORS com credenciais entre Vercel e Render, o que é justamente onde deploys falham. Em produção com dados reais eu inverteria: cookie `HttpOnly` com `SameSite`, CSRF token e, provavelmente, um BFF no Next.

Mitigação parcial já existente: o token é curto, e cada rota protegida revalida o papel **contra o banco** em vez de confiar apenas na afirmação do JWT. Remover ou rebaixar um usuário tem efeito imediato, sem esperar o token expirar.

---

## Erros e operação

### Contrato único de erro

Toda falha responde `{"error": {"code", "message"}}`. O frontend lê `code` quando precisa decidir e `message` quando precisa falar com o usuário — nunca interpreta texto livre.

Descartei devolver o corpo de validação do Pydantic: ele expõe nomes de campo internos e tipos esperados, informação de desenvolvedor vazando para a tela.

O catálogo completo, com os 51 códigos e prints de cada caso na interface, está em [erros.md](erros.md).

### Sobre "nunca retornar 500"

Não prometo isso, e a recusa é deliberada. Se o PostgreSQL cair no meio de uma requisição, 500 é a resposta **correta** — qualquer outra estaria mentindo sobre o que aconteceu.

O que garanto é que nenhum 500 é **não tratado**: todos seguem o contrato, nenhum expõe stack trace ou mensagem de exceção, e todos são registrados no servidor com método, caminho e `exc_info`.

Essa distinção veio de um achado real. Ao fechar essa lacuna descobri que `FastAPI(debug=...)` derivava de `ENVIRONMENT`, cujo padrão é `development` — e com `debug=True` o Starlette responde o traceback completo, com caminhos absolutos do disco, **ignorando qualquer handler**. Publicar sem definir a variável teria vazado o rastro de execução pela rede. A aplicação não passa mais `debug` ao FastAPI; o traceback vai para o log.

---

## Testes

Priorizei poucos testes sobre as regras que, se quebrarem, quebram o produto — não cobertura ampla de getters.

A divisão em duas suítes é intencional. A rápida não depende de serviço externo e roda em segundos. A integrada sobe um PostgreSQL isolado, em `tmpfs`, na porta 5433, e só ela pode provar concorrência: **conflito de lock não existe em banco mockado**. Um teste de overselling com repositório falso testaria o mock, não a regra.

O executor da suíte integrada recusa qualquer banco cujo nome não contenha `test`, e a checagem acontece antes de qualquer conexão, porque o reset é destrutivo. O reset descarta e recria o schema em vez de usar `alembic downgrade base` — o downgrade da migration `20260816_0002` recria a constraint única de `payments.reservation_id`, que os próprios cenários violam ao registrar várias tentativas na mesma reserva.

---

## O que eu faria em seguida

Em ordem de valor, se o projeto continuasse:

1. **Expiração automática também para reservas por quantidade.** Hoje só holds de assento expiram; uma reserva por quantidade abandonada segura estoque até cancelamento manual.
2. **Correlação de requisição ponta a ponta.** Frontend e backend registram falhas, mas sem ID comum. Rastrear um erro relatado por usuário exige cruzar horário e rota na mão.
3. **Sessão em cookie `HttpOnly` com CSRF**, aposentando o `localStorage`.
4. **Armazenamento de imagens externo** (S3 ou R2). Disco local impede mais de uma instância do backend.
5. **CI no GitHub Actions** rodando lint, build e as duas suítes a cada push.
6. **Rate limiting** em login, pagamento e portaria.
