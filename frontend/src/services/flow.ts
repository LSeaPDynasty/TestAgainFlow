import axios from 'axios';

// 类型定义
export interface Flow {
  id: number;
  name: string;
  description?: string;
  flow_type: 'standard' | 'dsl' | 'python';
  requires?: string[];
  default_params?: Record<string, any>;
  dsl_content?: string;
  py_file?: string;
  step_count: number;
  expanded_step_count: number;
  tags: any[];
  referenced_by_testcase_count: number;
  created_at: string;
  updated_at: string;
}

export interface FlowDetail extends Flow {
  steps: FlowStep[];
}

export interface FlowStep {
  order: number;
  step_id: number;
  step_name: string;
  action_type: string;
  screen_name?: string;
  element_name?: string;
  override_value?: string;
}

export interface FlowCreate {
  name: string;
  description?: string;
  flow_type: 'standard' | 'dsl' | 'python';
  dsl_content?: string;
  requires?: string[];
  default_params?: Record<string, any>;
  steps?: Array<{ step_id: number; order: number; override_value?: string }>;
  tag_ids?: number[];
}

export interface DslValidateResponse {
  valid: boolean;
  errors: string[];
  expanded_steps: any[];
  expanded_count: number;
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取流程列表
export const getFlows = (params?: {
  page?: number;
  page_size?: number;
  flow_type?: string;
  tag_ids?: string;
  search?: string;
  include_stats?: boolean;
  project_id?: number;
}) => {
  return api.get('/flows', { params });
};

// 获取流程详情
export const getFlow = (id: number) => {
  return api.get(`/flows/${id}`);
};

// 创建流程
export const createFlow = (data: FlowCreate) => {
  return api.post('/flows', data);
};

// 更新流程
export const updateFlow = (id: number, data: Partial<FlowCreate>) => {
  return api.put(`/flows/${id}`, data);
};

// 删除流程
export const deleteFlow = (id: number) => {
  return api.delete(`/flows/${id}`);
};

// 复制流程
export const duplicateFlow = (id: number, data: { new_name: string }) => {
  return api.post(`/flows/${id}/duplicate`, data);
};

// 验证DSL
export const validateDsl = (data: { dsl_content: string }) => {
  return api.post('/flows/validate-dsl', data);
};
