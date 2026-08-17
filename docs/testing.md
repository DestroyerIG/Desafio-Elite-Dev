# Estratégia de testes

## Suíte rápida

A suíte padrão não depende de serviços externos. Ela cobre validações, segurança dos tokens,
RBAC, gateway simulado, repositórios e regras isoladas:

```powershell
cd backend
python -m pytest -q
```

Os testes marcados como `integration` permanecem ignorados nesse comando.

## Suíte integrada

Os cenários de transação e concorrência usam PostgreSQL real. O serviço `db_test` é isolado da
base de desenvolvimento, usa a porta `5433` e mantém seus dados em `tmpfs`.

```powershell
docker compose --profile test up -d --wait db_test
cd backend
python scripts/run_integration_tests.py
```

O executor verifica se o nome do banco contém `test`, recria o schema, aplica todas as migrations,
executa o seed e roda somente os testes marcados como `integration`. O mesmo bloqueio existe no
Pytest: definir `RUN_INTEGRATION_TESTS=1` apontando para uma base comum encerra a execução antes do
primeiro teste.

Para usar outra base isolada:

```powershell
$env:TEST_DATABASE_URL="postgresql+asyncpg://usuario:senha@localhost:5433/minha_base_test"
python scripts/run_integration_tests.py
```

## Matriz da Fase 6

| Regra crítica | Comprovação |
|---|---|
| CUSTOMER não cria evento | `test_customer_cannot_create_event` e `test_customer_cannot_create_custom_event` |
| Quantidade acima do estoque falha | `test_concurrent_reservations_do_not_oversell` |
| Duas reservas não ultrapassam a capacidade | `test_concurrent_reservations_do_not_oversell` |
| Pagamento recusado gera zero ingressos | `test_payment_issues_exact_ticket_quantity_and_protects_qr` |
| Pagamento aprovado gera exatamente N ingressos | `test_payment_issues_exact_ticket_quantity_and_protects_qr` |
| QR adulterado retorna `INVALID` | `test_sharing_and_gate_validation_are_secure_and_atomic` |
| Primeira validação retorna `VALID` | `test_sharing_and_gate_validation_are_secure_and_atomic` |
| Nova validação retorna `ALREADY_USED` | `test_sharing_and_gate_validation_are_secure_and_atomic` |
| Ingresso de outro evento retorna `WRONG_EVENT` | `test_sharing_and_gate_validation_are_secure_and_atomic` |
| Respostas de erro seguem contrato único | `test_error_contract.py` |

Os testes integrados também cobrem pagamento concorrente idempotente, reembolso concorrente,
expiração de assentos, disputa pelo mesmo lugar e upload de imagem de evento.
