import axios from 'axios';

// 类型定义
export type Execution = {
  id: number;
  run_type: 'testcase' | 'suite';
  target_name: string;
  target_id?: number;
  profile_name?: string;
  device_serial?: string;
  status: 'running' | 'passed' | 'failed' | 'skipped' | 'error';
  result_summary?: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
  };
  duration?: number;
  error_msg?: string;
  created_at: string;
  updated_at: string;
};

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取执行历史
export const getHistory = (params?: {
  page?: number;
  page_size?: number;
  status?: string;
  run_type?: string;
}) => {
  return api.get('/runs', { params });
};

// 获取执行详情
export const getExecution = (id: number) => {
  return api.get(`/runs/${id}`);
};

// 重跑
export const rerunExecution = (id: number) => {
  return api.post(`/runs`, {
    type: 'testcase',
    target_ids: [id]
  });
};
