import { z } from "zod";

export const publishEventSchema = z.object({
  capacity: z.coerce
    .number<number>()
    .int("A capacidade deve ser um número inteiro.")
    .positive("A capacidade deve ser maior que zero."),
  ticketPrice: z.coerce
    .number<number>()
    .nonnegative("O preço não pode ser negativo."),
});

