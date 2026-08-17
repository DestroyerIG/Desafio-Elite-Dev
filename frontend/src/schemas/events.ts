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

const eventImageTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
export const MAX_EVENT_IMAGE_BYTES = 5 * 1024 * 1024;

export const customEventSchema = z.object({
  title: z
    .string()
    .trim()
    .min(2, "Informe um nome com pelo menos dois caracteres.")
    .max(255, "O nome deve ter no máximo 255 caracteres."),
  description: z
    .string()
    .trim()
    .max(10_000, "A descrição deve ter no máximo 10.000 caracteres."),
  venueName: z
    .string()
    .trim()
    .min(2, "Informe o nome do local.")
    .max(255, "O nome do local deve ter no máximo 255 caracteres."),
  venueAddress: z
    .string()
    .trim()
    .min(2, "Informe o endereço do evento.")
    .max(2_000, "O endereço deve ter no máximo 2.000 caracteres."),
  eventDate: z.string().refine((value) => {
    const date = new Date(value);
    return !Number.isNaN(date.getTime()) && date.getTime() > Date.now();
  }, "Informe uma data e um horário futuros."),
  capacity: z.coerce
    .number<number>()
    .int("A capacidade deve ser um número inteiro.")
    .positive("A capacidade deve ser maior que zero.")
    .max(1_000_000, "A capacidade máxima é de 1.000.000 de ingressos."),
  ticketPrice: z.coerce
    .number<number>()
    .nonnegative("O preço não pode ser negativo."),
  image: z
    .custom<File | null>(
      (value) => value === null || value instanceof File,
      "Selecione uma imagem válida.",
    )
    .refine(
      (file) => !file || eventImageTypes.has(file.type),
      "A imagem deve ser JPEG, PNG ou WebP.",
    )
    .refine(
      (file) => !file || file.size <= MAX_EVENT_IMAGE_BYTES,
      "A imagem deve ter no máximo 5 MB.",
    ),
});
