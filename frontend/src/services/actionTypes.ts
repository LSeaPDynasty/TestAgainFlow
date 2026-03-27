/**
 * Action Types API Service
 * 操作类型API服务 - 从后端动态获取操作类型定义
 */

import api from './api';

// ============ Types ============

export interface ActionTypeConfig {
  type_code: string;
  display_name: string;
  category?: string;
  description?: string;
  color?: string;
  requires_element: boolean;
  requires_value: boolean;
  config_schema?: any;
  first_seen_executor_id?: string;
  first_seen_at: string;
  is_deprecated: boolean;
  created_at: string;
  updated_at: string;
  supported_by_executors: string[];
}

export interface ActionTypesResponse {
  total: number;
  items: ActionTypeConfig[];
  categories: Record<string, string[]>;
}

export interface ActionCapabilityCheckRequest {
  executor_id?: string;
  action_types: string[];
}

export interface ActionCapabilityCheckResponse {
  is_supported: boolean;
  executor_id?: string;
  supported_actions: string[];
  unsupported_actions: string[];
  can_execute: boolean;
  warnings: string[];
}

export interface TestcaseValidationRequest {
  testcase_id: number;
  executor_id?: string;
  skip_unsupported?: boolean;
}

export interface TestcaseValidationResponse {
  testcase_id: number;
  testcase_name: string;
  can_execute: boolean;
  executor_id?: string;
  all_actions_supported: boolean;
  unsupported_actions: Array<{
    action_type: string;
    step_count: number;
  }>;
  warnings: string[];
  recommendation: string;
}

// ============ API Functions ============

/**
 * 获取所有操作类型列表
 */
export const getActionTypes = async (params?: {
  include_deprecated?: boolean
}): Promise<ActionTypesResponse> => {
  const response = await api.get('/executor-capabilities/action-types', {
    params: {
      include_deprecated: params?.include_deprecated || false,
    },
  });
  return response.data.data;
};

/**
 * 检查操作能力是否支持
 */
export const checkCapability = async (
  request: ActionCapabilityCheckRequest
): Promise<ActionCapabilityCheckResponse> => {
  const response = await api.post('/executor-capabilities/check-capability', request);
  return response.data.data;
};

/**
 * 验证用例是否可以在执行器上执行
 */
export const validateTestcase = async (
  request: TestcaseValidationRequest
): Promise<TestcaseValidationResponse> => {
  const response = await api.post('/executor-capabilities/validate-testcase', request);
  return response.data.data;
};

// ============ Utilities ============

/**
 * 将操作类型列表转换为分类映射（兼容旧代码）
 */
export const actionTypesToCategories = (
  items: ActionTypeConfig[]
): Record<string, string[]> => {
  const categories: Record<string, string[]> = {};

  for (const item of items) {
    const category = item.category || '未分类';
    if (!categories[category]) {
      categories[category] = [];
    }
    categories[category].push(item.type_code);
  }

  return categories;
};

/**
 * 将操作类型列表转换为颜色映射（兼容旧代码）
 */
export const actionTypesToColors = (
  items: ActionTypeConfig[]
): Record<string, string> => {
  const colors: Record<string, string> = {};

  for (const item of items) {
    if (item.color) {
      colors[item.type_code] = item.color;
    }
  }

  return colors;
};

/**
 * 检查操作类型是否需要元素
 */
export const actionRequiresElement = (
  actionType: string,
  items: ActionTypeConfig[]
): boolean => {
  const action = items.find(item => item.type_code === actionType);
  return action?.requires_element ?? false;
};

/**
 * 检查操作类型是否需要值
 */
export const actionRequiresValue = (
  actionType: string,
  items: ActionTypeConfig[]
): boolean => {
  const action = items.find(item => item.type_code === actionType);
  return action?.requires_value ?? false;
};
