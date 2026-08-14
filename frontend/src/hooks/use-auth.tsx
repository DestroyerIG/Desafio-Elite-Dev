"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  ApiError,
  clearAccessToken,
  getAccessToken,
  setAccessToken,
  subscribeAccessToken,
} from "@/services/api";
import { currentUserRequest, loginRequest } from "@/services/auth";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const token = useSyncExternalStore(
    subscribeAccessToken,
    getAccessToken,
    () => null,
  );

  const userQuery = useQuery({
    queryKey: ["auth", "me", token],
    queryFn: () => currentUserRequest(token as string),
    enabled: Boolean(token),
    retry: false,
  });

  useEffect(() => {
    if (userQuery.error instanceof ApiError && userQuery.error.status === 401) {
      clearAccessToken();
    }
  }, [userQuery.error]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: userQuery.data ?? null,
      isLoading: Boolean(token) && userQuery.isLoading,
      login: async (email, password) => {
        const response = await loginRequest(email, password);
        setAccessToken(response.access_token);
        queryClient.setQueryData(
          ["auth", "me", response.access_token],
          response.user,
        );
        return response.user;
      },
      logout: () => {
        clearAccessToken();
        queryClient.removeQueries({ queryKey: ["auth"] });
      },
    }),
    [queryClient, token, userQuery.data, userQuery.isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  return context;
}
