import api, { AUTH_TOKEN_KEY, AUTH_USER_KEY } from './api';

export interface UserInfo {
  id: number;
  username: string;
  email?: string | null;
  role: 'member' | 'admin' | 'super_admin' | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  role?: 'admin' | 'member';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

export const getAccessToken = (): string | null => localStorage.getItem(AUTH_TOKEN_KEY);

export const setAuthSession = (payload: TokenResponse) => {
  localStorage.setItem(AUTH_TOKEN_KEY, payload.access_token);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(payload.user));
};

export const clearAuthSession = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
};

export const getStoredUser = (): UserInfo | null => {
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    return null;
  }
};

export const isAuthenticated = (): boolean => Boolean(getAccessToken());

export const login = async (payload: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post('/users/login', payload);
  const data = response.data.data as TokenResponse;
  setAuthSession(data);
  return data;
};

export const register = async (payload: RegisterRequest): Promise<UserInfo> => {
  const response = await api.post('/users/register', payload);
  return response.data.data as UserInfo;
};

export const getMe = async (): Promise<UserInfo> => {
  const response = await api.get('/users/me');
  const user = response.data.data as UserInfo;
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  return user;
};

export const getUsers = async (): Promise<UserInfo[]> => {
  const response = await api.get('/users');
  return response.data.data as UserInfo[];
};

/**
 * 检查用户是否是管理员
 */
export const isAdmin = (user: UserInfo | null): boolean => {
  if (!user) return false;
  return user.role === 'admin' || user.role === 'super_admin';
};

/**
 * 检查用户是否是超级管理员
 */
export const isSuperAdmin = (user: UserInfo | null): boolean => {
  if (!user) return false;
  return user.role === 'super_admin';
};
