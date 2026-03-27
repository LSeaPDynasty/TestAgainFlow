import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取执行日志
export const getRunLogs = (taskId: string) => {
  return api.get(`/run-logs/${taskId}`);
};
