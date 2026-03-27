import axios from 'axios';

// 类型定义
export type ReportStats = {
  total_executions: number;
  pass_rate: number;
  avg_duration: number;
  top_failing_testcase?: {
    name: string;
    fail_count: number;
  };
};

export type TrendData = {
  date: string;
  passed: number;
  failed: number;
};

export type FailureRanking = {
  testcase_name: string;
  fail_count: number;
  last_failed_time: string;
  last_failure_reason: string;
};

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取报告统计
export const getReportStats = (params?: {
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/stats', { params });
};

// 获取趋势数据
export const getTrendData = (params?: {
  start_date?: string;
  end_date?: string;
  group_by?: 'day' | 'week';
}) => {
  return api.get('/reports/trends', { params });
};

// 获取失败排行
export const getFailureRanking = (params?: {
  start_date?: string;
  end_date?: string;
  limit?: number;
}) => {
  return api.get('/reports/failure-ranking', { params });
};
