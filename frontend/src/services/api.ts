import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "../store/authStore";
import type { APIErrorBody, APIResponse, AuthPayload } from "../types/api";

const baseURL = import.meta.env.VITE_API_URL || "";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

let refreshPromise: Promise<string | null> | null = null;

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIErrorBody>) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status;
    const isAuthRoute = original?.url?.includes("/auth/login") || original?.url?.includes("/auth/register");
    if (status === 401 && original && !original._retry && !isAuthRoute) {
      original._retry = true;
      const newToken = await refreshAccessToken();
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  },
);

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) return null;
      try {
        const response = await axios.post<APIResponse<AuthPayload>>(
          `${baseURL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken },
        );
        const { tokens, user } = response.data.data;
        useAuthStore.getState().setAuth(tokens.access_token, tokens.refresh_token, user);
        return tokens.access_token;
      } catch {
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

function detailMessage(item: unknown): string | null {
  if (!item || typeof item !== "object" || !("msg" in item)) return null;
  const raw = String((item as { msg: unknown }).msg).trim();
  if (!raw) return null;
  return raw.replace(/^Value error,\s*/i, "");
}

export function getErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as APIErrorBody | undefined;
    const details = Array.isArray(body?.error?.details)
      ? body.error.details.map(detailMessage).filter((msg): msg is string => Boolean(msg))
      : [];
    if (details.length) return details.join(". ");
    if (body?.error?.message) return body.error.message;
  }
  if (error instanceof Error) return error.message;
  return fallback;
}
