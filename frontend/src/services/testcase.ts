import axios from 'axios';

// 类型定义
export interface Testcase {
  id: number;
  name: string;
  description?: string;
  priority: string;
  timeout: number;
  enabled: boolean;
  params?: Record<string, any>;
  tags: any[];
  setup_flow_count: number;
  main_flow_count: number;
  teardown_flow_count: number;
  step_count: number;
  testcase_item_count: number;
  estimated_duration: number;
  suite_count: number;
  created_at: string;
  updated_at: string;
}

export interface TestcaseFlow {
  id: number;
  flow_id: number;
  flow_name?: string;
  flow_role: 'setup' | 'main' | 'teardown';
  order: number;
  enabled: boolean;
  params?: Record<string, any>;
}

export interface TestcaseItem {
  id: number;
  testcase_id: number;
  item_type: 'flow' | 'step';
  flow_id?: number;
  step_id?: number;
  order_index: number;
  enabled: boolean;
  continue_on_error?: boolean;
  params?: Record<string, any>;
  flow_name?: string;
  step_name?: string;
  step_action_type?: string;
  created_at: string;
  updated_at: string;
}

export interface TestcaseDetail extends Testcase {
  setup_flows: TestcaseFlow[];
  main_flows: TestcaseFlow[];
  teardown_flows: TestcaseFlow[];
  testcase_items?: TestcaseItem[];
  inline_steps: any[];
}

export interface TestcaseCreate {
  name: string;
  description?: string;
  priority: string;
  timeout?: number;
  enabled?: boolean;
  params?: Record<string, any>;
  setup_flows?: Array<{ flow_id: number; order: number; enabled?: boolean; params?: Record<string, any> }>;
  main_flows?: Array<{ flow_id: number; order: number; enabled?: boolean; params?: Record<string, any> }>;
  teardown_flows?: Array<{ flow_id: number; order: number; enabled?: boolean; params?: Record<string, any> }>;
  inline_steps?: Array<{ step_id: number; order: number }>;
  tag_ids?: number[];
}

export interface DependencyChain {
  setup_flows: any[];
  main_flows: any[];
  teardown_flows: any[];
  all_steps: any[];
  required_profiles: string[];
}

export interface RecursiveImportResult {
  count: number;
  failed: Array<{ name: string; error: string }>;
  details: {
    created: Record<string, string[]>;
    reused: Record<string, string[]>;
  };
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取用例列表
export const getTestcases = (params?: {
  page?: number;
  page_size?: number;
  priority?: string;
  tag_id?: number;
  tag_ids?: string;
  search?: string;
  include_stats?: boolean;
  project_id?: number;
}) => {
  return api.get('/testcases', { params });
};

// 获取用例详情
export const getTestcase = (id: number) => {
  return api.get(`/testcases/${id}`);
};

// 创建用例
export const createTestcase = (data: TestcaseCreate) => {
  return api.post('/testcases', data);
};

// 更新用例
export const updateTestcase = (id: number, data: Partial<TestcaseCreate>) => {
  return api.put(`/testcases/${id}`, data);
};

// 删除用例
export const deleteTestcase = (id: number) => {
  return api.delete(`/testcases/${id}`);
};

// 复制用例
export const duplicateTestcase = (id: number, data: { new_name: string }) => {
  return api.post(`/testcases/${id}/duplicate`, data);
};

// 获取依赖链
export const getDependencyChain = (id: number) => {
  return api.get(`/testcases/${id}/dependency-chain`);
};

// JSON递归导入（单个或批量）
export const importTestcasesBatch = (data: Record<string, any>) => {
  return api.post('/testcases/batch', data);
};

// 获取用例的 testcase_items
export const getTestcaseItems = (testcaseId: number) => {
  return api.get(`/testcases/${testcaseId}/items`);
};

// 更新用例的 testcase_items（全量替换）
export const updateTestcaseItems = (testcaseId: number, items: Array<{
  item_type: 'flow' | 'step';
  flow_id?: number;
  step_id?: number;
  order_index: number;
  enabled?: boolean;
  continue_on_error?: boolean;
  params?: Record<string, any>;
}>) => {
  return api.put(`/testcases/${testcaseId}/items`, { items });
};
