import axios from 'axios';

// 类型定义
export type Device = {
  id: number;
  name: string;
  serial: string;
  model?: string;
  os_version?: string;
  status: 'online' | 'offline' | 'unauthorized' | 'unknown';
  connection_type: 'USB' | 'TCP/IP';
  ip_port?: string;
  capabilities?: string[];
  created_at: string;
  updated_at: string;
};

export type DeviceCreate = {
  name: string;
  serial: string;
  model?: string;
  os_version?: string;
  connection_type: 'USB' | 'TCP/IP';
  ip_port?: string;
  capabilities?: string[];
};

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取设备列表
export const getDevices = (params?: {
  page?: number;
  page_size?: number;
  status?: string;
}) => {
  return api.get('/devices', { params });
};

// 获取设备详情
export const getDevice = (id: number) => {
  return api.get(`/devices/${id}`);
};

// 创建设备
export const createDevice = (data: DeviceCreate) => {
  return api.post('/devices', data);
};

// 更新设备
export const updateDevice = (id: number, data: Partial<DeviceCreate>) => {
  return api.put(`/devices/${id}`, data);
};

// 删除设备
export const deleteDevice = (id: number) => {
  return api.delete(`/devices/${id}`);
};

// 刷新设备状态
export const refreshDevices = () => {
  return api.post('/devices/refresh');
};

// 测试设备连接
export const testDeviceConnection = (serial: string) => {
  return api.post(`/devices/${serial}/test`);
};

// 获取设备DOM
export const getDeviceDom = (serial: string) => {
  return api.get(`/devices/${serial}/dom`);
};
