// Authentication API functions

import api from './api';
import {
  AuthUser,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  PasswordChangeRequest,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
  User,
} from '@/types/auth';

export const authApi = {
  /**
   * Register a new user
   */
  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await api.post<RegisterResponse>('/auth/register', data);
    return response.data;
  },

  /**
   * Login user
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/login', data);
    return response.data;
  },

  /**
   * Logout user
   */
  logout: async (): Promise<LogoutResponse> => {
    const response = await api.post<LogoutResponse>('/auth/logout');
    return response.data;
  },

  /**
   * Get current user
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Refresh access token
   */
  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Change password
   */
  changePassword: async (data: PasswordChangeRequest): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/change-password', data);
    return response.data;
  },
};

export default authApi;
