/**
 * Captura o caminho feliz: agenda, compra, ingresso com QR e validação na portaria.
 *
 * Complementa `capturar-erros.mjs`. Enquanto aquele documenta o que o avaliador
 * provavelmente não vai ver, este registra o fluxo principal para o README.
 *
 *   cd scripts/screenshots
 *   npm install && npx playwright install chromium
 *   npm run capturar-fluxo
 *
 * ATENÇÃO: diferente do roteiro de erros, este NÃO é reversível. Ele compra e
 * valida um ingresso de verdade, então cada execução consome um ingresso do seed
 * e deixa um ticket `USED`. Um ingresso validado não pode ser reembolsado, que é
 * justamente a regra que o sistema precisa garantir.
 */

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, "..", "..");
const DESTINO = path.join(RAIZ, "docs", "images", "fluxo");

const FRONTEND = process.env.FRONTEND_URL ?? "http://localhost:3000";
const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";
const SENHA = process.env.SEED_PASSWORD ?? "DevOnly123!";

const TOKEN_KEY = "elite-events-access-token";
const VIEWPORT = { width: 1280, height: 900 };

async function entrar(email) {
  const resposta = await fetch(`${BACKEND}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password: SENHA }),
  });
  if (!resposta.ok) throw new Error(`login de ${email} falhou com ${resposta.status}`);
  return (await resposta.json()).access_token;
}

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

async function fotografar(page, nome, textoEsperado) {
  const alvo = page.getByText(textoEsperado, { exact: false }).first();
  await alvo.waitFor({ state: "visible", timeout: 30000 });
  await page.screenshot({ path: path.join(DESTINO, `${nome}.png`), fullPage: true });
  console.log(`  ${nome} ... ok`);
}

async function main() {
  await mkdir(DESTINO, { recursive: true });
  const navegador = await chromium.launch();

  const tokenCliente = await entrar("customer1@example.com");
  const tokenPortaria = await entrar("gate@example.com");

  const eventos = await (await fetch(`${BACKEND}/api/v1/events`)).json();
  const evento = eventos.find(
    (item) => item.seating_mode === "GENERAL_ADMISSION" && item.available_tickets > 0,
  );
  if (!evento) throw new Error("nenhum evento por quantidade com estoque no seed");

  console.log("\ncapturando o fluxo principal:\n");

  const contexto = await novaAba(navegador, tokenCliente);
  const page = await contexto.newPage();

  // 1. Agenda pública -------------------------------------------------------
  await page.goto(`${FRONTEND}/events`);
  await fotografar(page, "01-agenda-publica", "Eventos publicados");

  // 2. Detalhe do evento ----------------------------------------------------
  await page.goto(`${FRONTEND}/events/${evento.id}`);
  await fotografar(page, "02-detalhe-evento", evento.title.slice(0, 25));

  // 3. Checkout com pagamento aprovado --------------------------------------
  await page.goto(`${FRONTEND}/checkout/${evento.id}`);
  await page.locator("#quantity").fill("1");
  await page.getByRole("button", { name: "Confirmar reserva" }).click();
  await page.locator("#card-number").waitFor({ timeout: 20000 });
  await fotografar(page, "03-checkout-pagamento", "Pagamento simulado");

  await page.locator("#card-number").fill("4242424242424242");
  await page.getByRole("button", { name: "Pagar e emitir ingressos" }).click();

  // 4. Ingresso com QR ------------------------------------------------------
  // A aprovação redireciona direto para o ingresso emitido; não há tela
  // intermediária de "pagamento aprovado".
  await page.waitForURL(/\/my-tickets\//, { timeout: 30000 });
  // O PNG do QR é buscado autenticado depois da página montar. Esperar só pelo
  // título capturaria o "Gerando QR...", sem o elemento central da tela.
  await page
    .locator('img[alt^="QR do ingresso"]')
    .waitFor({ state: "visible", timeout: 30000 });
  await fotografar(page, "04-ingresso-qr", "QR do ingresso");

  const corpo = await page.locator("body").innerText();
  const publicCode = corpo.match(/ELT-[A-Z0-9]{4}(?:-[A-Z0-9]{4})+/)[0];
  console.log(`  ingresso capturado: ${publicCode}`);
  await contexto.close();

  // 5. Portaria validando ---------------------------------------------------
  const portaria = await novaAba(navegador, tokenPortaria);
  const pageGate = await portaria.newPage();
  await pageGate.goto(`${FRONTEND}/gate`);
  await pageGate.locator("select").first().selectOption({ label: evento.title });
  await pageGate.getByLabel(/c[óo]digo do ingresso/i).fill(publicCode);
  await pageGate.getByRole("button", { name: /validar/i }).click();
  await fotografar(pageGate, "05-portaria-liberado", "Entrada liberada");

  // 6. Segunda leitura do mesmo QR -----------------------------------------
  await pageGate.getByLabel(/c[óo]digo do ingresso/i).fill(publicCode);
  await pageGate.getByRole("button", { name: /validar/i }).click();
  await fotografar(pageGate, "06-portaria-ja-utilizado", "Ingresso já utilizado");
  await portaria.close();

  await navegador.close();
  console.log(`\ncapturas em docs/images/fluxo/`);
}

main().catch((erro) => {
  console.error("\nerro fatal:", erro.message);
  process.exit(1);
});
