import api from './api';

// 类型定义
export type Screen = {
  id: number;
  name: string;
  activity?: string;
  description?: string;
  project_id?: number;
  element_count: number;
  created_at: string;
  updated_at: string;
};

export type ScreenCreate = {
  name: string;
  description?: string;
  project_id?: number;
};

// 获取界面列表
export const getScreens = (params?: {
  page?: number;
  page_size?: number;
  project_id?: number;
  search?: string;
}) => {
  return api.get('/screens', { params });
};

// 获取界面详情
export const getScreen = (id: number) => {
  return api.get(`/screens/${id}`);
};

// 创建界面
export const createScreen = (data: ScreenCreate) => {
  return api.post('/screens', data);
};

// 更新界面
export const updateScreen = (id: number, data: Partial<ScreenCreate>) => {
  return api.put(`/screens/${id}`, data);
};

// 删除界面
export const deleteScreen = (id: number) => {
  return api.delete(`/screens/${id}`);
};
