// Authentication types.

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  email_verified: boolean;
  last_login_at?: string;
  created_at: string;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  email_verified: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  user: AuthUser;
  tokens: TokenResponse;
}

export interface RegisterResponse {
  user: AuthUser;
  tokens: TokenResponse;
  message: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface LogoutResponse {
  message: string;
}
