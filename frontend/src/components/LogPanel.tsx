import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Space, Empty, Tag } from 'antd';
import {
  CloseOutlined,
  ClearOutlined,
  DownloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
} from '@ant-design/icons';
import { useAppStore } from '../store/appStore';

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
  details?: string;
}

const LogPanel: React.FC = () => {
  const { logPanelVisible, toggleLogPanel } = useAppStore();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 模拟添加日志（实际应该从WebSocket或API获取）
  useEffect(() => {
    if (!logPanelVisible) return;

    const interval = setInterval(() => {
      if (isRunning) {
        const newLog: LogEntry = {
          timestamp: new Date().toLocaleTimeString(),
          level: ['info', 'success', 'warn', 'error'][Math.floor(Math.random() * 4)] as any,
          message: `测试执行中... ${Math.floor(Math.random() * 1000)}`,
          details: Math.random() > 0.7 ? '详细日志信息' : undefined,
        };
        setLogs((prev) => [...prev, newLog]);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [logPanelVisible, isRunning]);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const handleClear = () => {
    setLogs([]);
  };

  const handleExport = () => {
    const text = logs.map(log =>
      `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}${log.details ? '\n' + log.details : ''}`
    ).join('\n');

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `testflow-log-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'info': return 'blue';
      case 'success': return 'success';
      case 'warn': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  if (!logPanelVisible) return null;

  return (
    <Card
      title="执行日志"
      size="small"
      style={{
        position: 'fixed',
        bottom: 0,
        left: '200px',
        right: 0,
        height: '300px',
        zIndex: 999,
        borderTop: '1px solid #d9d9d9',
      }}
      extra={
        <Space size="small">
          <Button
            type="text"
            size="small"
            icon={isRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => setIsRunning(!isRunning)}
          >
            {isRunning ? '暂停' : '开始'}
          </Button>
          <Button
            type="text"
            size="small"
            icon={<ClearOutlined />}
            onClick={handleClear}
          >
            清空
          </Button>
          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            导出
          </Button>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={toggleLogPanel}
          />
        </Space>
      }
      bodyStyle={{
        padding: '8px 16px',
        height: 'calc(100% - 56px)',
        overflowY: 'auto',
      }}
    >
      <div ref={scrollRef} style={{ fontFamily: 'monospace', fontSize: '12px' }}>
        {logs.length === 0 ? (
          <Empty description="暂无日志" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          logs.map((log, index) => (
            <div
              key={index}
              style={{
                marginBottom: '4px',
                padding: '4px 8px',
                borderRadius: '4px',
                backgroundColor: log.level === 'error' ? '#fff2f0' : 'transparent',
              }}
            >
              <Space size="small">
                <span style={{ color: '#8c8c8c' }}>{log.timestamp}</span>
                <Tag color={getLevelColor(log.level)} style={{ margin: 0 }}>
                  {log.level.toUpperCase()}
                </Tag>
                <span>{log.message}</span>
              </Space>
              {log.details && (
                <div style={{ marginLeft: '24px', color: '#8c8c8c', marginTop: '4px' }}>
                  {log.details}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </Card>
  );
};

export default LogPanel;
