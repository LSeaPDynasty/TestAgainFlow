/**
 * Project service - 项目管理服务
 */
import api from './api';

export interface ProjectStatistics {
  testcase_count: number;
  suite_count: number;
  run_count: number;
  pass_count: number;
  pass_rate: number;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  status: string;
  tags: string[];
  owner_id?: number;
  priority: string;
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
  statistics?: ProjectStatistics;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  status?: string;
  tags?: string[];
  owner_id?: number;
  priority?: string;
  start_date?: string;
  end_date?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: string;
  tags?: string[];
  owner_id?: number;
  priority?: string;
  start_date?: string;
  end_date?: string;
}

export interface ProjectListParams {
  page?: number;
  page_size?: number;
  status?: string;
  priority?: string;
  search?: string;
}

/**
 * 获取项目列表
 */
export const getProjects = (params: ProjectListParams = {}) => {
  return api.get('/projects', { params });
};

/**
 * 创建项目
 */
export const createProject = (data: ProjectCreate) => {
  return api.post('/projects', data);
};

/**
 * 获取项目详情
 */
export const getProject = (id: number) => {
  return api.get(`/projects/${id}`);
};

/**
 * 更新项目
 */
export const updateProject = (id: number, data: ProjectUpdate) => {
  return api.put(`/projects/${id}`, data);
};

/**
 * 删除项目
 */
export const deleteProject = (id: number) => {
  return api.delete(`/projects/${id}`);
};

/**
 * 获取项目统计信息
 */
export const getProjectStatistics = (id: number) => {
  return api.get(`/projects/${id}/stats`);
};
