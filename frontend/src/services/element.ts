import axios from 'axios';
import { message } from 'antd';

// 类型定义
export type Locator = {
  id?: number;
  type: string;
  value: string;
  priority: number;
};

export type Element = {
  id: number;
  name: string;
  description?: string;
  screen_id: number;
  screen_name?: string;
  locators: Locator[];
  created_at: string;
  updated_at: string;
};

export type ElementCreate = {
  name: string;
  description?: string;
  screen_id: number;
  locators: Locator[];
};

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取元素列表
export const getElements = (params?: {
  page?: number;
  page_size?: number;
  screen_id?: number;
  search?: string;
}) => {
  return api.get('/elements', { params });
};

// 获取元素详情
export const getElement = (id: number) => {
  return api.get(`/elements/${id}`);
};

// 创建元素
export const createElement = (data: ElementCreate) => {
  return api.post('/elements', data);
};

// 更新元素
export const updateElement = (id: number, data: Partial<ElementCreate>) => {
  return api.put(`/elements/${id}`, data);
};

// 删除元素
export const deleteElement = (id: number) => {
  return api.delete(`/elements/${id}`);
};

// 测试元素定位符
export const testElementLocator = (id: number, data: {
  device_serial: string;
  locator_index?: number;
}) => {
  return api.post(`/elements/${id}/test`, data);
};
