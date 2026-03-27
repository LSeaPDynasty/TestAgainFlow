import api from './api';

export interface SchedulerConfig {
  enabled: boolean;
  max_inflight_tasks: number;
  default_priority: number;
  queue_strategy: string;
}

export interface SchedulerQueueState {
  queue_size: number;
  statuses: Record<string, string>;
}

export const getSchedulerConfig = async (): Promise<SchedulerConfig> => {
  const response = await api.get('/scheduler/config');
  return response.data.data as SchedulerConfig;
};

export const updateSchedulerConfig = async (
  payload: Partial<SchedulerConfig>,
): Promise<SchedulerConfig> => {
  const response = await api.put('/scheduler/config', payload);
  return response.data.data as SchedulerConfig;
};

export const getSchedulerQueueState = async (): Promise<SchedulerQueueState> => {
  const response = await api.get('/scheduler/queue');
  return response.data.data as SchedulerQueueState;
};
