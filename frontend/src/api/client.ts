import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export interface AuthSessionTokens {
  access: string;
  refresh: string;
}

type AuthHandlers = {
  getTokens: () => AuthSessionTokens | null;
  setTokens: (tokens: AuthSessionTokens) => void;
  logout: () => void;
};

let authHandlers: AuthHandlers = {
  getTokens: () => null,
  setTokens: () => undefined,
  logout: () => undefined
};

let refreshPromise: Promise<string | null> | null = null;

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000
});

export function registerAuthHandlers(handlers: AuthHandlers) {
  authHandlers = handlers;
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const tokens = authHandlers.getTokens();
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const tokens = authHandlers.getTokens();

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && tokens?.refresh) {
      originalRequest._retry = true;

      if (!refreshPromise) {
        refreshPromise = axios
          .post<{ access: string; refresh?: string }>(`${API_BASE_URL}/auth/refresh/`, {
            refresh: tokens.refresh
          })
          .then((response) => {
            const nextTokens = {
              access: response.data.access,
              refresh: response.data.refresh ?? tokens.refresh
            };
            authHandlers.setTokens(nextTokens);
            return nextTokens.access;
          })
          .catch(() => {
            authHandlers.logout();
            return null;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const access = await refreshPromise;
      if (access) {
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      }
    }

    if (error.response?.status === 401) {
      authHandlers.logout();
    }

    return Promise.reject(error);
  }
);
