import axios from 'axios';

// 类型定义
export interface Profile {
  id: number;
  name: string;
  description?: string;
  data: Record<string, Record<string, string>>;
  tags: any[];
  is_global: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProfileCreate {
  name: string;
  description?: string;
  data: Record<string, Record<string, string>>;
  tag_ids?: number[];
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取环境配置列表
export const getProfiles = (params?: {
  page?: number;
  page_size?: number;
  tag_ids?: string;
  search?: string;
}) => {
  return api.get('/profiles', { params });
};

// 获取环境配置详情
export const getProfile = (id: number) => {
  return api.get(`/profiles/${id}`);
};

// 创建环境配置
export const createProfile = (data: ProfileCreate) => {
  return api.post('/profiles', data);
};

// 更新环境配置
export const updateProfile = (id: number, data: Partial<ProfileCreate>) => {
  return api.put(`/profiles/${id}`, data);
};

// 删除环境配置
export const deleteProfile = (id: number) => {
  return api.delete(`/profiles/${id}`);
};
