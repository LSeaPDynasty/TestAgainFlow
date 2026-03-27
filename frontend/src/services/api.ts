import axios, { type AxiosError } from 'axios';
import { message } from 'antd';

export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

export interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export const AUTH_TOKEN_KEY = 'testflow_access_token';
export const AUTH_USER_KEY = 'testflow_user';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const clearAuthAndRedirect = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  if (window.location.pathname !== '/login') {
    window.location.replace('/login');
  }
};

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiResponse<unknown>;
    if (payload?.code === 0) {
      return response;
    }

    const isLoginApi = response.config.url?.includes('/users/login');
    const isRegisterApi = response.config.url?.includes('/users/register');
    const isAuthFailure = payload?.code === 4001;

    if (isAuthFailure && !isLoginApi && !isRegisterApi) {
      message.error(payload?.message || 'Authentication expired');
      clearAuthAndRedirect();
    } else {
      message.error(payload?.message || 'Request failed');
    }

    return Promise.reject(new Error(payload?.message || 'Request failed'));
  },
  (error: AxiosError<ApiResponse>) => {
    if (error.response?.status === 401) {
      message.error('Unauthorized');
      clearAuthAndRedirect();
      return Promise.reject(error);
    }

    if (error.response) {
      message.error(error.response.data?.message || 'Network error');
    } else if (error.request) {
      message.error('Unable to connect to server');
    } else {
      message.error('Request config error');
    }

    return Promise.reject(error);
  },
);

export default api;
