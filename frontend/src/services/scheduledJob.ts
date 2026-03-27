import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 类型定义
export interface ScheduledJob {
  id: number;
  name: string;
  description?: string;
  job_type: 'testcase' | 'suite';
  target_id: number;
  target_name?: string;
  cron_expression: string;
  device_serial?: string;
  enabled: boolean;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'disabled';
  last_run_time?: string;
  next_run_time?: string;
  last_run_status?: string;
  last_run_message?: string;
  project_id?: number;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface ScheduledJobCreate {
  name: string;
  description?: string;
  job_type: 'testcase' | 'suite';
  target_id: number;
  cron_expression: string;
  device_serial?: string;
  enabled?: boolean;
  project_id?: number;
}

export interface ScheduledJobUpdate {
  name?: string;
  description?: string;
  job_type?: 'testcase' | 'suite';
  target_id?: number;
  cron_expression?: string;
  device_serial?: string;
  enabled?: boolean;
  project_id?: number;
}

// 获取定时任务列表
export const getScheduledJobs = (params?: {
  page?: number;
  page_size?: number;
  enabled_only?: boolean;
  project_id?: number;
}) => {
  return api.get('/scheduled-jobs', { params });
};

// 获取定时任务详情
export const getScheduledJob = (id: number) => {
  return api.get(`/scheduled-jobs/${id}`);
};

// 创建定时任务
export const createScheduledJob = (data: ScheduledJobCreate) => {
  return api.post('/scheduled-jobs', data);
};

// 更新定时任务
export const updateScheduledJob = (id: number, data: ScheduledJobUpdate) => {
  return api.put(`/scheduled-jobs/${id}`, data);
};

// 删除定时任务
export const deleteScheduledJob = (id: number) => {
  return api.delete(`/scheduled-jobs/${id}`);
};

// 手动运行定时任务
export const runScheduledJob = (id: number, deviceSerial: string) => {
  return api.post(`/scheduled-jobs/${id}/run`, { device_serial: deviceSerial });
};

// 切换定时任务启用状态
export const toggleScheduledJob = (id: number) => {
  return api.post(`/scheduled-jobs/${id}/toggle`);
};
