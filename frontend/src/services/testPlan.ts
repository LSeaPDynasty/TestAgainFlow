import api, { type ApiResponse, type PaginatedResponse } from './api';

// 类型定义
export interface TestPlan {
  id: number;
  name: string;
  description?: string;
  execution_strategy: 'sequential' | 'parallel';
  max_parallel_tasks: number;
  enabled: boolean;
  project_id?: number;
  suite_count: number;
  created_at: string;
  updated_at: string;
}

export interface TestPlanDetail extends TestPlan {
  suites: TestPlanSuiteDetail[];
}

export interface TestPlanSuite {
  suite_id: number;
  suite_name?: string;
  order: number;
  enabled: boolean;
  execution_config?: Record<string, unknown>;
}

export interface TestPlanTestcaseOrder {
  testcase_id: number;
  testcase_name?: string;
  order_index: number;
  priority?: string;
}

export interface TestPlanSuiteDetail {
  id: number;
  test_plan_id: number;
  suite_id: number;
  suite_name?: string;
  order_index: number;
  enabled: boolean;
  testcases: TestPlanTestcaseOrder[];
}

export interface TestPlanCreate {
  name: string;
  description?: string;
  execution_strategy?: 'sequential' | 'parallel';
  max_parallel_tasks?: number;
  enabled?: boolean;
  project_id?: number;
  suites?: TestPlanSuite[];
}

export interface TestPlanUpdate {
  name?: string;
  description?: string;
  execution_strategy?: 'sequential' | 'parallel';
  max_parallel_tasks?: number;
  enabled?: boolean;
  suites?: TestPlanSuite[];
}

export interface TestPlanExecuteRequest {
  platform: string;
  device_serial?: string;
  profile_id?: number;
  timeout?: number;
  extra_args?: Record<string, unknown>;
  priority?: string;
}

// 获取测试计划列表
export const getTestPlans = (params?: {
  page?: number;
  page_size?: number;
  project_id?: number;
}) => {
  return api.get<ApiResponse<PaginatedResponse<TestPlan>>>('/test-plans', { params });
};

// 获取测试计划详情
export const getTestPlan = (id: number) => {
  return api.get<ApiResponse<TestPlanDetail>>(`/test-plans/${id}`);
};

// 创建测试计划
export const createTestPlan = (data: TestPlanCreate) => {
  return api.post<ApiResponse<TestPlan>>('/test-plans', data);
};

// 更新测试计划
export const updateTestPlan = (id: number, data: TestPlanUpdate) => {
  return api.put<ApiResponse<TestPlan>>(`/test-plans/${id}`, data);
};

// 删除测试计划
export const deleteTestPlan = (id: number) => {
  return api.delete<ApiResponse>(`/test-plans/${id}`);
};

// 切换测试计划启用状态
export const toggleTestPlan = (id: number, enabled: boolean) => {
  return api.patch<ApiResponse<TestPlan>>(`/test-plans/${id}/toggle`, { enabled });
};

// 添加套件到测试计划
export const addSuitesToPlan = (id: number, suite_ids: number[]) => {
  return api.post<ApiResponse<TestPlanDetail>>(`/test-plans/${id}/suites`, { suite_ids });
};

// 从测试计划移除套件
export const removeSuitesFromPlan = (id: number, suite_ids: number[]) => {
  return api.delete<ApiResponse<TestPlanDetail>>(`/test-plans/${id}/suites`, { data: { suite_ids } });
};

// 调整套件顺序
export const reorderPlanSuites = (id: number, suites: TestPlanSuite[]) => {
  return api.put<ApiResponse<TestPlanDetail>>(`/test-plans/${id}/suites/reorder`, { suites });
};

// 设置用例顺序
export const setSuiteTestcaseOrder = (
  planId: number,
  suiteId: number,
  testcase_orders: TestPlanTestcaseOrder[]
) => {
  return api.put<ApiResponse<TestPlanDetail>>(
    `/test-plans/${planId}/suites/${suiteId}/testcases/order`,
    { testcase_orders }
  );
};

// 执行测试计划
export const executeTestPlan = (id: number, data: TestPlanExecuteRequest) => {
  return api.post<ApiResponse<RunResponse[]>>(`/test-plans/${id}/run`, data);
};

// 执行响应类型
export interface RunResponse {
  task_id: string;
  type: string;
  targets: Array<{ id: number; name: string }>;
  status: string;
  cmd: string[];
  started_at: string;
}
