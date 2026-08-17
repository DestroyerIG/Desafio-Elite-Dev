# Uso de IA

O desenvolvimento deste projeto teve assistência do OpenAI Codex.

A IA foi usada para:

- ler e organizar os requisitos do roadmap;
- propor a estrutura inicial do repositório;
- auxiliar a modelagem relacional e a definição de constraints;
- gerar o scaffold de configuração, migration, seed e documentação;
- executar verificações automatizadas e relatar limitações do ambiente;
- consultar a documentação oficial dos frameworks e da Ticketmaster;
- auxiliar a implementação e revisão de autenticação, RBAC e integração externa;
- construir os fluxos públicos e do organizador no frontend;
- criar testes unitários e integrados e diagnosticar inconsistências nos dados de seed;
- implementar o fluxo transacional de reservas e revisar a ordem de locks;
- construir o checkout do cliente e seus estados de confirmação e cancelamento;
- elaborar e executar testes concorrentes reais contra PostgreSQL;
- diagnosticar reutilização de conexões entre event loops e estado antigo no identity map do SQLAlchemy.
- implementar a abstração de pagamento simulado e revisar a atomicidade entre pagamento e emissão;
- estruturar tokens de ingresso assinados, persistência por hash e geração autenticada de QR;
- criar a área de ingressos no frontend com carregamento seguro da imagem protegida;
- ampliar testes para recusa, quantidade exata, idempotência, propriedade e adulteração de token.
- evoluir a cardinalidade de pagamentos com migration para preservar múltiplas tentativas por reserva;
- implementar recuperação de reservas pendentes e nova tentativa de pagamento sem duplicar cobrança ou ingresso;
- validar tentativas concorrentes de pagamento e a visibilidade privada do histórico de reservas.
- implementar compartilhamento por token opaco com persistência apenas de hash;
- revisar a ordem transacional e criar testes concorrentes para validação única na portaria;
- construir leitura local de QR pela câmera, fallback manual e feedback dos quatro resultados obrigatórios.
- modelar setores, assentos, vínculos históricos e constraints de exclusividade;
- implementar holds temporários, expiração automática e integração transacional com pagamento, cancelamento e reembolso;
- estruturar atualização em tempo real com PostgreSQL `LISTEN/NOTIFY`, WebSocket, versionamento e fallback por polling;
- construir o editor do organizador, o mapa acessível do cliente, o cronômetro e a identificação do assento nos ingressos;
- validar migration reversível, concorrência pelo mesmo lugar e devolução exata ao estoque em PostgreSQL isolado.

As sugestões precisam ser revisadas como qualquer contribuição de código. Decisões de produto, credenciais reais e aprovação para avançar entre fases continuam sob controle do responsável pelo projeto.
