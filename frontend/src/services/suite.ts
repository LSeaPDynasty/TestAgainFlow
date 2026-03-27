import api from './api';

// 类型定义
export interface Suite {
  id: number;
  name: string;
  description?: string;
  enabled: boolean;
  tags: any[];
  testcase_count: number;
  total_step_count: number;
  estimated_duration: number;
  created_at: string;
  updated_at: string;
}

export interface SuiteDetail extends Suite {
  testcases: Array<{
    id: number;
    name: string;
    priority: string;
    enabled: boolean;
    order: number;
  }>;
}

export interface SuiteCreate {
  name: string;
  description?: string;
  enabled?: boolean;
  testcase_ids?: number[];
  tag_ids?: number[];
}

// 获取套件列表
export const getSuites = (params?: {
  page?: number;
  page_size?: number;
  tag_ids?: string;
  search?: string;
  include_stats?: boolean;
  project_id?: number;
}) => {
  return api.get('/suites', { params });
};

// 获取套件详情
export const getSuite = (id: number) => {
  return api.get(`/suites/${id}`);
};

// 创建套件
export const createSuite = (data: SuiteCreate) => {
  return api.post('/suites', data);
};

// 更新套件
export const updateSuite = (id: number, data: Partial<SuiteCreate>) => {
  return api.put(`/suites/${id}`, data);
};

// 删除套件
export const deleteSuite = (id: number) => {
  return api.delete(`/suites/${id}`);
};

// 复制套件
export const duplicateSuite = (id: number, data: { new_name: string }) => {
  return api.post(`/suites/${id}/duplicate`, data);
};
