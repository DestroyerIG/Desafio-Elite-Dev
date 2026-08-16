import { z } from "zod";


export const gateValidationSchema = z.object({
  eventId: z.uuid("Selecione o evento da entrada."),
  credential: z
    .string()
    .trim()
    .min(1, "Informe o QR ou código do ingresso.")
    .max(2048, "O conteúdo informado é muito longo."),
});
