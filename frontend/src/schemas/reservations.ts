import { z } from "zod";

export const reservationSchema = z.object({
  quantity: z.coerce
    .number({ error: "Informe uma quantidade válida." })
    .int("A quantidade precisa ser um número inteiro.")
    .min(1, "Selecione pelo menos um ingresso."),
});
