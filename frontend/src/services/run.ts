import axios from 'axios';

// 类型定义
export interface RunHistory {
  id: number;
  task_id: string;
  type: string;
  target_id: number;
  target_name: string;
  device_serial: string;
  device_name?: string;
  result: 'pending' | 'running' | 'pass' | 'fail' | 'stopped' | 'timeout';
  started_at: string;
  finished_at?: string;
  duration?: number;
  returncode?: number;
}

export interface RunCreate {
  type: 'testcase' | 'suite';
  target_ids: number[];
  device_serial?: string;
  profile_id?: number;
  timeout?: number;
  extra_args?: string;
  config?: {
    stop_on_failure?: boolean;
    screenshot_on_failure?: boolean;
    max_retries?: number;
  };
}

export interface RunStatus {
  task_id: string;
  status: string;
  progress: number;
  current_step?: string;
  result?: string;
  total_count: number;
  success_count: number;
  failed_count: number;
  started_at: string;
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取执行历史列表
export const getRunHistories = (params?: {
  page?: number;
  page_size?: number;
  status?: string;
  device_serial?: string;
}) => {
  return api.get('/runs', { params });
};

// 获取执行历史详情
export const getRunHistory = (id: number) => {
  return api.get(`/runs/${id}`);
};

// 创建执行任务
export const createRun = (data: RunCreate) => {
  return api.post('/runs', data);
};

// 获取任务状态
export const getRunStatus = (taskId: string) => {
  return api.get(`/runs/${taskId}/status`);
};

// 停止任务
export const stopRun = (taskId: string) => {
  return api.post(`/runs/${taskId}/stop`, {});
};

// 暂停任务
export const pauseRun = (taskId: string) => {
  return api.post(`/runs/${taskId}/pause`, {});
};

// 恢复任务
export const resumeRun = (taskId: string) => {
  return api.post(`/runs/${taskId}/resume`, {});
};

// 批量执行用例
export const batchRunTestcases = (data: {
  testcase_ids: number[];
  device_serial: string;
  config?: {
    stop_on_failure?: boolean;
    screenshot_on_failure?: boolean;
    max_retries?: number;
  };
}) => {
  return api.post('/runs/batch-testcases', data);
};

// 批量执行套件
export const batchRunSuites = (data: {
  suite_ids: number[];
  device_serial: string;
  config?: {
    stop_on_failure?: boolean;
    screenshot_on_failure?: boolean;
    max_retries?: number;
  };
}) => {
  return api.post('/runs/batch-suites', data);
};
