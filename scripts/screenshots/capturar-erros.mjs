/**
 * Captura as telas de erro da aplicação em execução.
 *
 * O objetivo é documentar o que o usuário vê quando algo falha. Como um avaliador
 * normalmente só encontra o caminho feliz, estas imagens são a evidência de que os
 * casos de erro foram tratados.
 *
 * Pré-requisitos: aplicação no ar (`docker compose up -d`) e seed aplicado.
 *
 *   cd scripts/screenshots
 *   npm install && npx playwright install chromium
 *   npm run capturar
 *
 * Cada cenário é independente: uma falha não impede os demais. O relatório final
 * lista o que foi capturado e o que não foi.
 */

import { chromium } from "playwright";
import { execFile } from "node:child_process";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const executar = promisify(execFile);

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, "..", "..");
const DESTINO = path.join(RAIZ, "docs", "images", "erros");

const FRONTEND = process.env.FRONTEND_URL ?? "http://localhost:3000";
const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";
const SENHA = process.env.SEED_PASSWORD ?? "DevOnly123!";
const CONTAINER_BACKEND = process.env.BACKEND_CONTAINER ?? "desafioelitedev-backend-1";

const TOKEN_KEY = "elite-events-access-token";
const VIEWPORT = { width: 1280, height: 900 };

const capturados = [];
const falhados = [];

async function entrar(email) {
  const resposta = await fetch(`${BACKEND}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password: SENHA }),
  });
  if (!resposta.ok) {
    throw new Error(`login de ${email} falhou com ${resposta.status}`);
  }
  const { access_token: token } = await resposta.json();
  return token;
}

/** Injeta o token antes de qualquer script da página, como se o usuário já estivesse logado. */
async function novaAba(navegador, token) {
  const contexto = await navegador.newContext({ viewport: VIEWPORT, locale: "pt-BR" });
  if (token) {
    await contexto.addInitScript(
      ([chave, valor]) => window.localStorage.setItem(chave, valor),
      [TOKEN_KEY, token],
    );
  }
  return contexto;
}

async function cenario(nome, descricao, executarCenario) {
  process.stdout.write(`  ${nome} ... `);
  try {
    await executarCenario();
    capturados.push({ nome, descricao });
    console.log("ok");
  } catch (erro) {
    falhados.push({ nome, motivo: erro.message });
    console.log(`FALHOU (${erro.message})`);
  }
}

/**
 * Fotografa só depois que `textoEsperado` está visível na página.
 *
 * Ancorar em `getByRole("alert")` não funciona: a página mantém uma região
 * `role="alert"` vazia desde o primeiro render, então o seletor resolvia em ~1s e
 * a foto saía no estado de carregamento. Além disso o TanStack Query repete a
 * requisição antes de desistir, e o erro só aparece alguns segundos depois.
 *
 * Ancorar no texto resolve os dois problemas e transforma cada captura numa
 * asserção: se a mensagem mudar, o roteiro falha em vez de gerar uma imagem errada.
 */
async function fotografar(page, nome, textoEsperado) {
  const alvo = page.getByText(textoEsperado, { exact: false }).first();
  await alvo.waitFor({ state: "visible", timeout: 30000 });
  await alvo.scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(DESTINO, `${nome}.png`), fullPage: true });
}

async function main() {
  await mkdir(DESTINO, { recursive: true });
  const navegador = await chromium.launch();

  const tokenCliente = await entrar("customer1@example.com");
  const tokenOrganizador = await entrar("organizer@example.com");
  const tokenPortaria = await entrar("gate@example.com");

  const eventos = await (await fetch(`${BACKEND}/api/v1/events`)).json();
  const evento = eventos.find((item) => item.seating_mode === "GENERAL_ADMISSION");
  if (!evento) throw new Error("nenhum evento por quantidade encontrado no seed");

  console.log("\ncapturando cenários:\n");

  // --- 404 de rota: app/not-found.tsx -------------------------------------
  await cenario(
    "404-rota-inexistente",
    "URL que não corresponde a nenhuma rota",
    async () => {
      const contexto = await novaAba(navegador, null);
      const page = await contexto.newPage();
      await page.goto(`${FRONTEND}/uma-rota-que-nao-existe`);
      await fotografar(page, "404-rota-inexistente", "Este endereço não existe");
      await contexto.close();
    },
  );

  // --- 404 de recurso: EVENT_NOT_FOUND ------------------------------------
  await cenario(
    "404-evento-inexistente",
    "EVENT_NOT_FOUND — identificador válido, evento inexistente",
    async () => {
      const contexto = await novaAba(navegador, null);
      const page = await contexto.newPage();
      await page.goto(`${FRONTEND}/events/00000000-0000-4000-8000-000000000000`);
      await fotografar(page, "404-evento-inexistente", "Evento não encontrado.");
      await contexto.close();
    },
  );

  // --- 401: credenciais inválidas no login --------------------------------
  await cenario(
    "401-credenciais-invalidas",
    "INVALID_CREDENTIALS — e-mail ou senha incorretos",
    async () => {
      const contexto = await novaAba(navegador, null);
      const page = await contexto.newPage();
      await page.goto(`${FRONTEND}/login`);
      await page.getByLabel(/e-mail/i).fill("customer1@example.com");
      await page.getByLabel(/senha/i).fill("senha-errada");
      await page.getByRole("button", { name: /entrar/i }).click();
      await fotografar(page, "401-credenciais-invalidas", "E-mail ou senha inválidos.");
      await contexto.close();
    },
  );

  // --- 403 por papel: cliente tentando a área do organizador --------------
  await cenario(
    "403-papel-sem-permissao",
    "Guard de papel — cliente acessando a área do organizador",
    async () => {
      const contexto = await novaAba(navegador, tokenCliente);
      const page = await contexto.newPage();
      await page.goto(`${FRONTEND}/organizer/dashboard`);
      // O guard troca a rota; a prova é ter parado na agenda pública.
      await page.waitForURL(/\/events/, { timeout: 20000 });
      await fotografar(page, "403-papel-sem-permissao", "Eventos publicados");
      await contexto.close();
    },
  );

  // --- Catálogo externo indisponível --------------------------------------
  await cenario(
    "502-catalogo-externo-indisponivel",
    "Família CATALOG_* — a Ticketmaster recusa ou não responde",
    async () => {
      const contexto = await novaAba(navegador, tokenOrganizador);
      const page = await contexto.newPage();
      // Entrar direto na rota disputa com o guard, que redireciona enquanto a auth
      // não resolveu. Navegar pelo menu, como um usuário real, evita a corrida.
      await page.goto(`${FRONTEND}/organizer/dashboard`);
      await page.getByRole("link", { name: "Publicar evento" }).click();
      // A página abre no modo "criar meu evento"; a importação fica atrás do alternador.
      await page.getByRole("button", { name: "Importar da Ticketmaster" }).click();
      await page.locator("#catalog-query").fill("rock");
      await page.getByRole("button", { name: "Pesquisar" }).click();
      await fotografar(page, "502-catalogo-externo-indisponivel", "A chave da Ticketmaster não está configurada no backend.");
      await contexto.close();
    },
  );

  // --- 409 de estoque: INSUFFICIENT_TICKETS -------------------------------
  await cenario(
    "409-ingressos-insuficientes",
    "INSUFFICIENT_TICKETS — quantidade acima do estoque disponível",
    async () => {
      // O input limita a quantidade ao estoque que a página carregou, então digitar
      // um número grande é barrado pelo navegador. O caminho realista é o dado
      // defasado: a página abre com N disponíveis, outro cliente compra enquanto
      // esta permanece aberta, e o envio de N só é recusado pelo servidor. É
      // exatamente o motivo de a validação do frontend não bastar.
      const contexto = await novaAba(navegador, tokenCliente);
      const page = await contexto.newPage();
      await page.goto(`${FRONTEND}/checkout/${evento.id}`);
      await page.locator("#quantity").waitFor();

      const atual = await (await fetch(`${BACKEND}/api/v1/events/${evento.id}`)).json();
      const disponivel = atual.available_tickets;
      const concorrente = await entrar("customer2@example.com");
      const resposta = await fetch(
        `${BACKEND}/api/v1/events/${evento.id}/reservations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${concorrente}`,
          },
          body: JSON.stringify({ quantity: disponivel - 1 }),
        },
      );
      const reservaConcorrente = await resposta.json();

      try {
        await page.locator("#quantity").fill(String(disponivel));
        await page.getByRole("button", { name: "Confirmar reserva" }).click();
        await fotografar(page, "409-ingressos-insuficientes", "Não existem ingressos suficientes disponíveis.");
      } finally {
        // Devolve o estoque para não deixar o seed alterado.
        if (reservaConcorrente?.id) {
          await fetch(`${BACKEND}/api/v1/reservations/${reservaConcorrente.id}/cancel`, {
            method: "POST",
            headers: { Authorization: `Bearer ${concorrente}` },
          });
        }
        await contexto.close();
      }
    },
  );

  // --- 402: pagamento recusado --------------------------------------------
  await cenario(
    "402-pagamento-recusado",
    "PAYMENT_DECLINED — cartão de teste terminado em 0000",
    async () => {
      const contexto = await novaAba(navegador, tokenCliente);
      const page = await contexto.newPage();
      await page.goto(`${FRONTEND}/checkout/${evento.id}`);
      await page.locator("#quantity").fill("1");
      // Guarda o id da reserva criada para devolver o estoque no final: sem isso
      // cada execução deixaria uma reserva PENDENTE segurando um ingresso.
      const criacao = page.waitForResponse(
        (r) => r.url().includes("/reservations") && r.request().method() === "POST",
      );
      await page.getByRole("button", { name: "Confirmar reserva" }).click();
      const reserva = await (await criacao).json().catch(() => null);
      // Cartão terminado em 0000 é a regra de recusa do gateway simulado.
      const cartao = page.locator("#card-number");
      await cartao.waitFor({ timeout: 20000 });
      await cartao.fill("4111111111110000");
      await page.getByRole("button", { name: "Pagar e emitir ingressos" }).click();
      try {
        await fotografar(page, "402-pagamento-recusado", "Pagamento recusado. Confira os dados do cartão");
      } finally {
        if (reserva?.id) {
          await fetch(`${BACKEND}/api/v1/reservations/${reserva.id}/cancel`, {
            method: "POST",
            headers: { Authorization: `Bearer ${tokenCliente}` },
          });
        }
        await contexto.close();
      }
    },
  );

  // --- Portaria: ingresso inválido ----------------------------------------
  await cenario(
    "portaria-ingresso-invalido",
    "INVALID — código digitado que não corresponde a nenhum ingresso",
    async () => {
      const contexto = await novaAba(navegador, tokenPortaria);
      const page = await contexto.newPage();
      await page.goto(`${FRONTEND}/gate`);
      await page.locator("select").first().selectOption({ index: 1 });
      const codigo = page.getByLabel(/c[óo]digo/i).first();
      await codigo.fill("ELT-0000-0000");
      await page.getByRole("button", { name: /validar/i }).first().click();
      await fotografar(page, "portaria-ingresso-invalido", "Ingresso inválido");
      await contexto.close();
    },
  );

  // --- Backend fora do ar --------------------------------------------------
  // Precisa ser o último: derruba o backend e o religa em seguida.
  await cenario(
    "backend-fora-do-ar",
    "Falha de conexão — o navegador não alcança a API",
    async () => {
      await executar("docker", ["stop", CONTAINER_BACKEND]);
      try {
        const contexto = await novaAba(navegador, null);
        const page = await contexto.newPage();
        await page.goto(`${FRONTEND}/events`);
        // O TanStack Query repete antes de desistir; o alerta só aparece no fim.
        await fotografar(page, "backend-fora-do-ar", "Não foi possível carregar os eventos.");
        await contexto.close();
      } finally {
        await executar("docker", ["start", CONTAINER_BACKEND]);
      }
    },
  );

  await navegador.close();

  console.log(`\n${capturados.length} capturado(s) em docs/images/erros/`);
  for (const item of capturados) console.log(`  - ${item.nome}.png — ${item.descricao}`);
  if (falhados.length) {
    console.log(`\n${falhados.length} não capturado(s):`);
    for (const item of falhados) console.log(`  - ${item.nome}: ${item.motivo}`);
    process.exitCode = 1;
  }
}

main().catch((erro) => {
  console.error("\nerro fatal:", erro.message);
  process.exit(1);
});
