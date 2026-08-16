import { apiRequest } from "@/services/api";
import type { GateValidation } from "@/types/api";


export function validateGateTicket(eventId: string, credential: string) {
  return apiRequest<GateValidation>("/api/v1/gate/validate", {
    method: "POST",
    body: JSON.stringify({ event_id: eventId, credential }),
  });
}
