// API client configuration

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// How long the session-present cookie lives (matches backend refresh window).
const SESSION_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

export const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

/** Read a persisted field from the zustand auth store. */
function getStored(field: 'accessToken' | 'refreshToken'): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem('auth-storage');
    if (!stored) return null;
    return JSON.parse(stored)?.state?.[field] ?? null;
  } catch {
    return null;
  }
}

/**
 * Persist refreshed tokens into the store + middleware cookie.
 * The refresh token is rotated by the backend, so we store the new one too.
 */
function persistTokens(accessToken: string, refreshToken?: string): void {
  if (typeof window === 'undefined') return;
  try {
    const stored = localStorage.getItem('auth-storage');
    if (stored) {
      const parsed = JSON.parse(stored);
      parsed.state = {
        ...(parsed.state || {}),
        accessToken,
        isAuthenticated: true,
        ...(refreshToken ? { refreshToken } : {}),
      };
      localStorage.setItem('auth-storage', JSON.stringify(parsed));
    }
  } catch {
    // ignore write errors
  }
  document.cookie = `access_token=${accessToken}; path=/; max-age=${SESSION_MAX_AGE}; SameSite=Lax`;
}

/** Wipe all client-side auth state (used when the session is truly gone). */
function clearSession(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('auth-storage');
  document.cookie = 'access_token=; path=/; max-age=0; SameSite=Lax';
}

// Request interceptor - attach Bearer token
api.interceptors.request.use(
  (config) => {
    const token = getStored('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Single-flight refresh: if many requests 401 at once, only one /auth/refresh runs.
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  // Bare client (no interceptors) so a 401 here can't recurse into itself.
  // Send the stored refresh token in the body — this works cross-site (Vercel
  // frontend -> Railway backend), where the http-only cookie would not be sent.
  // withCredentials is kept so the cookie still works for same-origin/dev setups.
  const storedRefresh = getStored('refreshToken');
  const response = await axios.post(
    `${API_BASE_URL}/api/v1/auth/refresh`,
    storedRefresh ? { refresh_token: storedRefresh } : {},
    { withCredentials: true, headers: { 'Content-Type': 'application/json' } }
  );
  const token: string | undefined = response.data?.access_token;
  if (!token) throw new Error('No access token returned from refresh');
  persistTokens(token, response.data?.refresh_token);
  return token;
}

// Response interceptor — silently refresh the access token on 401, then retry.
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;
    const url = original?.url || '';

    // Never try to refresh for the auth endpoints themselves.
    const isAuthEndpoint =
      url.includes('/auth/login') ||
      url.includes('/auth/register') ||
      url.includes('/auth/refresh');

    if (
      status === 401 &&
      original &&
      !original._retry &&
      !isAuthEndpoint &&
      typeof window !== 'undefined'
    ) {
      original._retry = true;
      try {
        refreshPromise = refreshPromise ?? refreshAccessToken();
        const newToken = await refreshPromise;
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (refreshError) {
        // Refresh token is gone/expired → session is genuinely over.
        clearSession();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        refreshPromise = null;
      }
    }

    // 401 we couldn't recover from (e.g. retry already failed).
    if (status === 401 && !isAuthEndpoint && typeof window !== 'undefined') {
      clearSession();
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default api;
