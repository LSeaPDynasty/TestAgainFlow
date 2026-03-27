import axios from 'axios';

// 类型定义
export type Step = {
  id: number;
  name: string;
  description?: string;
  screen_id: number;
  screen_name?: string;
  element_id?: number;
  element_name?: string;
  action_type: string;
  action_value?: string;
  assertions?: any[];
  wait_time?: number;
  created_at: string;
  updated_at: string;
};

export type StepCreate = {
  name: string;
  description?: string;
  screen_id: number;
  element_id?: number;
  action_type: string;
  action_value?: string;
  assertions?: any[];
  wait_time?: number;
};

const ACTION_TYPES = [
  // 设备操作
  'click',
  'long_press',
  'input',
  'swipe',
  'hardware_back',
  // 等待
  'wait_element',
  'wait_time',
  // 断言
  'assert_text',
  'assert_exists',
  'assert_not_exists',
  'assert_color',
  // 控制流
  'repeat',
  'break_if',
  'set',
  'call',
  // 系统
  'start_activity',
  'screenshot',
];

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取步骤列表
export const getSteps = (params?: {
  page?: number;
  page_size?: number;
  search?: string;
  screen_id?: number;
  action_type?: string;
  tag_ids?: string;
  project_id?: number;
}) => {
  return api.get('/steps', { params });
};

// 获取步骤详情
export const getStep = (id: number) => {
  return api.get(`/steps/${id}`);
};

// 创建步骤
export const createStep = (data: StepCreate) => {
  return api.post('/steps', data);
};

// 更新步骤
export const updateStep = (id: number, data: Partial<StepCreate>) => {
  return api.put(`/steps/${id}`, data);
};

// 删除步骤
export const deleteStep = (id: number) => {
  return api.delete(`/steps/${id}`);
};

export { ACTION_TYPES };
