import { useEffect, useState, useRef } from 'react';
import { message } from 'antd';

export interface TaskLog {
  level: string;
  message: string;
  timestamp?: number;
  testcase_id?: number;
  testcase_name?: string;
  testcase_result?: string;
}

export interface TaskLogsOptions {
  taskId: string;
  enabled?: boolean;
  onLog?: (log: TaskLog) => void;
  onComplete?: () => void;
}

export function useTaskLogs({ taskId, enabled = true, onLog, onComplete }: TaskLogsOptions) {
  const [logs, setLogs] = useState<TaskLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  useEffect(() => {
    if (!enabled || !taskId) {
      return;
    }

    const connect = () => {
      const wsUrl = `ws://localhost:8000/ws/task-queue`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected for task logs');
        setIsConnected(true);

        // 发送订阅请求（如果后端支持）
        // ws.send(JSON.stringify({ type: 'subscribe_logs', task_id: taskId }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // 过滤出我们关注任务的日志
          if (data.type === 'task_log' && data.task_id === taskId) {
            const log: TaskLog = data.log;
            setLogs((prev) => [...prev, log]);
            onLog?.(log);
          }

          // 任务完成
          if (data.type === 'task_complete' && data.task_id === taskId) {
            console.log('Task completed:', data.result);
            onComplete?.();
          }

        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsConnected(false);

        // 5秒后尝试重连
        reconnectTimeoutRef.current = setTimeout(() => {
          if (enabled) {
            connect();
          }
        }, 5000);
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      // 清理
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [taskId, enabled, onLog, onComplete]);

  return {
    logs,
    isConnected,
    clearLogs: () => setLogs([]),
  };
}
