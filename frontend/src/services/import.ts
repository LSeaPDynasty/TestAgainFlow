import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 导入可能需要更长时间
});

// 批量导入
export const bulkImport = (data: any) => {
  return api.post('/import/bulk', data);
};

// 导入元素到指定界面
export const importElements = (data: any) => {
  return api.post('/import/elements', data);
};

// 上传文件导入
export const uploadImportFile = (file: File, options?: {
  skip_existing?: boolean;
  create_screens?: boolean;
}) => {
  const formData = new FormData();
  formData.append('file', file);
  if (options?.skip_existing !== undefined) {
    formData.append('skip_existing', String(options.skip_existing));
  }
  if (options?.create_screens !== undefined) {
    formData.append('create_screens', String(options.create_screens));
  }

  return api.post('/import/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 下载JSON模板
export const downloadJsonTemplate = () => {
  return api.get('/import/template/json', {
    responseType: 'blob',
  });
};

// 下载YAML模板
export const downloadYamlTemplate = () => {
  return api.get('/import/template/yaml', {
    responseType: 'blob',
  });
};

// 下载元素导入模板
export const downloadElementsOnlyTemplate = () => {
  return api.get('/import/template/elements-only', {
    responseType: 'blob',
  });
};
