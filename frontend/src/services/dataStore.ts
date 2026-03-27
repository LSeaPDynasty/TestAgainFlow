import axios from 'axios';

// 类型定义
export interface DataStore {
  [env: string]: {
    [key: string]: string;
  };
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 获取数据存储
export const getDataStore = () => {
  return api.get('/data-store');
};

// 更新数据存储
export const updateDataStore = (data: DataStore) => {
  return api.put('/data-store', data);
};

// 导入数据
export const importData = (data: {
  env: string;
  key: string;
  value: string;
}) => {
  return api.post('/data-store/import', data);
};

// 清空数据
export const clearDataStore = () => {
  return api.post('/data-store/clear', {});
};
