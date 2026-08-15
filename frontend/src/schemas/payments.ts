import { z } from "zod";

export const paymentSchema = z.object({
  cardNumber: z
    .string()
    .transform((value) => value.replace(/[\s-]/g, ""))
    .refine(
      (value) => /^\d{13,19}$/.test(value),
      "Informe um número de cartão com 13 a 19 dígitos.",
    ),
});
