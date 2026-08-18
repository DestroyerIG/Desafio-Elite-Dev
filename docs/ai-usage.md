# Uso de IA

O desenvolvimento contou com assistência de IA (OpenAI Codex nas fases iniciais, Claude nas finais). O enunciado do desafio recomenda transparência sobre isso, então este documento separa o que foi **decisão** do que foi **execução**.

A distinção importa porque é ela que responde à pergunta que o avaliador de fato quer fazer: quem entendeu o problema?

## Decisões que foram minhas

Estas não saíram de sugestão automática. São escolhas de projeto, com alternativas descartadas conscientemente — o raciocínio de cada uma está em [decisoes-e-alternativas.md](decisoes-e-alternativas.md).

- **Escopo e ordem de execução.** Fechar o fluxo completo — publicar, reservar, pagar, emitir, compartilhar, validar — antes de abrir qualquer frente nova. Assentos marcados só depois do caminho principal pronto.
- **Ingresso por quantidade primeiro**, entre as duas opções que o enunciado permitia.
- **Consistência garantida no banco**, não na aplicação: lock pessimista na reserva e na validação do ingresso.
- **`LISTEN/NOTIFY` em vez de Redis** para o tempo real, aceitando a ausência de durabilidade em troca de não adicionar um componente de infraestrutura.
- **Um ticket por unidade comprada**, em vez de contador na reserva.
- **Gateway de pagamento atrás de um contrato**, com o simulador como única implementação.
- **QR assinado com segredo próprio e apenas hash persistido**, separado do segredo de sessão.
- **JWT em `localStorage` no MVP**, com o custo em XSS assumido explicitamente e o caminho de evolução registrado.
- **Modelagem relacional final**: entidades, constraints e o que cada tabela protege.
- **Quais testes valem a pena**: concorrência real contra PostgreSQL em vez de cobertura ampla.
- **Recusar a meta "nunca retornar 500"**, trocando por "nenhum 500 não tratado" — uma alegação que resiste a pergunta.

## Onde a IA ajudou

- Ler o roadmap e organizar a sequência de entregas.
- Propor a estrutura inicial do repositório e o esqueleto dos módulos.
- Escrever a maior parte do código de rotas, schemas, services e repositories a partir das decisões acima.
- Consultar documentação oficial de FastAPI, SQLAlchemy, Alembic, Next.js e Ticketmaster.
- Escrever os testes, incluindo os cenários concorrentes contra PostgreSQL real.
- Redigir e revisar a documentação.
- Diagnosticar problemas que consumiriam tempo: reuso de conexão entre event loops nos testes, estado antigo no *identity map* do SQLAlchemy depois de esperar por lock, e ordem de locks para evitar deadlock.
- Auditar o tratamento de erros e capturar as telas de falha com Playwright.

## Achados que surgiram da revisão assistida

Vale registrar separadamente, porque são defeitos reais que uma revisão encontrou depois de o código estar "pronto":

- **`FastAPI(debug=...)` derivava de `ENVIRONMENT`**, cujo padrão é `development`. Com `debug=True`, o Starlette responde o traceback completo — caminhos absolutos do disco incluídos — e ignora qualquer handler de erro registrado. Publicar sem definir a variável teria vazado o rastro de execução pela rede.
- **Faltava handler para `Exception`**, então uma queda do banco quebrava o contrato de erro. O ramo que trataria isso existia, mas era código inalcançável.
- **A suíte integrada só rodava uma vez por contêiner.** O `alembic downgrade base` recria uma constraint única que os próprios testes violam.
- **`sslmode=require`**, formato que Neon e Supabase entregam, é recusado pelo asyncpg. Teria sido a primeira falha do deploy.
- **Enums crus na interface**: `PENDING` no checkout e `ALREADY_USED` na portaria chegavam à tela sem tradução.

## Limite

Sugestão de IA é tratada como qualquer contribuição de código: passa por revisão antes de entrar. Nada foi aceito por vir pronto — o critério é entender o que faz e conseguir defender por quê.

Credenciais reais, decisões de produto e a aprovação para avançar entre fases permaneceram sob controle do responsável pelo projeto.
