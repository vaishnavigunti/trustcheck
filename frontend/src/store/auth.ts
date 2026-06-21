// Authentication store using Zustand

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { authApi } from '@/lib/auth';
import { AuthUser, LoginRequest, RegisterRequest, User } from '@/types/auth';

/** Robustly extract the human-readable error message from any axios error shape. */
function extractErrorMessage(error: any, fallback: string): string {
  // No response at all = network/server-down error
  if (!error?.response) {
    if (error?.message === 'Network Error' || error?.code === 'ERR_NETWORK') {
      return 'Cannot connect to the server. Make sure the backend is running on port 8000.';
    }
    return error?.message || fallback;
  }

  const data = error.response?.data;
  if (!data) return fallback;

  // TrustCheck custom format:  { error: { message: "..." } }
  if (data?.error?.message) return data.error.message;

  // FastAPI HTTPException string:  { detail: "..." }
  if (typeof data?.detail === 'string') return data.detail;

  // FastAPI pydantic validation array:  { detail: [{ msg: "..." }] }
  if (Array.isArray(data?.detail) && data.detail.length > 0) {
    const first = data.detail[0];
    return first?.msg || first?.message || fallback;
  }

  // Plain message field
  if (typeof data?.message === 'string') return data.message;

  return fallback;
}

interface AuthState {
  // State
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  hasHydrated: boolean;
  accessToken: string | null;

  // Actions
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
  setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      hasHydrated: false,
      accessToken: null,

      // Hydration setter
      setHasHydrated: (value: boolean) => set({ hasHydrated: value }),

      // Login action
      login: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(data);
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            accessToken: response.tokens.access_token,
          });
        } catch (error: any) {
          set({
            error: extractErrorMessage(error, 'Login failed'),
            isLoading: false,
          });
          throw error;
        }
      },

      // Register action
      register: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.register(data);
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            accessToken: response.tokens.access_token,
          });
        } catch (error: any) {
          set({
            error: extractErrorMessage(error, 'Registration failed'),
            isLoading: false,
          });
          throw error;
        }
      },

      // Logout action
      logout: async () => {
        set({ isLoading: true });
        try {
          await authApi.logout();
        } catch (error) {
          // Ignore logout errors
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            accessToken: null,
          });
        }
      },

      // Fetch current user
      fetchCurrentUser: async () => {
        try {
          const user = await authApi.getCurrentUser();
          set({
            user: {
              id: user.id,
              email: user.email,
              full_name: user.full_name,
              is_active: user.is_active,
              email_verified: user.email_verified,
            },
            isAuthenticated: true,
          });
        } catch (error) {
          set({
            user: null,
            isAuthenticated: false,
          });
        }
      },

      // Clear error
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        accessToken: state.accessToken,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
