import axios from 'axios';

// 设备相关API
export const getDevices = (params: any) => {
  return axios.get('/api/v1/devices', { params });
};

export const createDevice = (data: any) => {
  return axios.post('/api/v1/devices', data);
};

export const updateDevice = (id: number, data: any) => {
  return axios.put(`/api/v1/devices/${id}`, data);
};

export const deleteDevice = (id: number) => {
  return axios.delete(`/api/v1/devices/${id}`);
};

export const refreshDevices = () => {
  return axios.post('/api/v1/devices/refresh');
};

export const testDeviceConnection = (serial: string) => {
  return axios.post('/api/v1/devices/test', { serial });
};

// 执行引擎相关API
export const getExecutorStatus = () => {
  return axios.get('/api/v1/executor/status');
};

export const getExecutorDevices = () => {
  return axios.get('/api/v1/executor/devices');
};

export const getActiveTasks = () => {
  return axios.get('/api/v1/executor/tasks');
};
