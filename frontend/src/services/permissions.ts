import api from './api';

export interface ProjectMember {
  id: number;
  project_id: number;
  user_id: number;
  username: string | null;
  email: string | null;
  role: 'viewer' | 'editor' | 'admin' | 'owner';
  joined_at: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AddProjectMemberRequest {
  username: string;
  role: 'viewer' | 'editor' | 'admin';
}

export interface UpdateMemberRoleRequest {
  role: 'viewer' | 'editor' | 'admin';
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  project_id: number | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  status: string;
  error_message: string | null;
  created_at: string | null;
}

export interface AuditLogsQuery {
  page?: number;
  page_size?: number;
  project_id?: number;
  resource_type?: string;
  resource_id?: number;
  action?: string;
}

/**
 * 获取项目成员列表
 */
export const getProjectMembers = async (projectId: number): Promise<ProjectMember[]> => {
  const response = await api.get(`/permissions/projects/${projectId}/members`);
  return response.data.data as ProjectMember[];
};

/**
 * 添加项目成员
 */
export const addProjectMember = async (
  projectId: number,
  data: AddProjectMemberRequest,
): Promise<ProjectMember> => {
  const response = await api.post(`/permissions/projects/${projectId}/members`, data);
  return response.data.data as ProjectMember;
};

/**
 * 更新成员角色
 */
export const updateMemberRole = async (
  projectId: number,
  userId: number,
  data: UpdateMemberRoleRequest,
): Promise<void> => {
  await api.put(`/permissions/projects/${projectId}/members/${userId}`, data);
};

/**
 * 移除项目成员
 */
export const removeProjectMember = async (projectId: number, userId: number): Promise<void> => {
  await api.delete(`/permissions/projects/${projectId}/members/${userId}`);
};

/**
 * 获取审计日志
 */
export const getAuditLogs = async (
  query: AuditLogsQuery = {},
): Promise<{ items: AuditLog[]; total: number }> => {
  const params = new URLSearchParams();
  if (query.page) params.append('page', query.page.toString());
  if (query.page_size) params.append('page_size', query.page_size.toString());
  if (query.project_id) params.append('project_id', query.project_id.toString());
  if (query.resource_type) params.append('resource_type', query.resource_type);
  if (query.resource_id) params.append('resource_id', query.resource_id.toString());
  if (query.action) params.append('action', query.action);

  const response = await api.get(`/permissions/audit-logs?${params.toString()}`);
  return response.data.data as { items: AuditLog[]; total: number };
};

/**
 * 获取用户有权限访问的项目ID列表
 */
export const getMyAccessibleProjects = async (): Promise<number[]> => {
  const response = await api.get('/permissions/my-projects');
  return response.data.data as number[];
};
