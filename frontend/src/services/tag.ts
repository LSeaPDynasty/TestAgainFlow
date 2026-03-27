import axios from 'axios';

// 类型定义
export interface Tag {
  id: number;
  name: string;
  color?: string;
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取标签列表
export const getTags = (params?: {
  page?: number;
  page_size?: number;
  search?: string;
}) => {
  return api.get('/tags', { params });
};

// 获取标签详情
export const getTag = (id: number) => {
  return api.get(`/tags/${id}`);
};

// 创建标签
export const createTag = (data: { name: string; color?: string }) => {
  return api.post('/tags', data);
};

// 更新标签
export const updateTag = (id: number, data: { name?: string; color?: string }) => {
  return api.put(`/tags/${id}`, data);
};

// 删除标签
export const deleteTag = (id: number) => {
  return api.delete(`/tags/${id}`);
};
