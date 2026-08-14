import { apiRequest } from "@/services/api";
import type { AuthResponse, User } from "@/types/api";

export function loginRequest(email: string, password: string) {
  return apiRequest<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function currentUserRequest(token: string) {
  return apiRequest<User>("/api/v1/auth/me", {}, token);
}

