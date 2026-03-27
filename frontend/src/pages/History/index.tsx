import React, { useState } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Progress,
  message,
  Modal,
  List,
  Empty,
  Spin,
} from 'antd';
import {
  ReloadOutlined,
  PlayCircleOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  MinusCircleOutlined,
  EyeOutlined,
  CloseOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRunHistories,
  createRun,
} from '../../services/run';
import type { RunHistory as Execution } from '../../services/run';
import SuiteReport from '../../components/SuiteReport';
import { useTaskLogs, type TaskLog } from '../../hooks/useTaskLogs';
import DrawerSelector from '../../components/DrawerSelector';

const History: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();
  const [selectedType, setSelectedType] = useState<string | undefined>();
  const [reportVisible, setReportVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Execution | null>(null);
  const [logsModalVisible, setLogsModalVisible] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // 获取执行历史
  const { data: historyData, isLoading } = useQuery({
    queryKey: ['run-histories', page, pageSize, selectedStatus, selectedType],
    queryFn: () =>
      getRunHistories({
        page,
        page_size: pageSize,
        status: selectedStatus,
        device_serial: undefined,
      }),
    refetchInterval: 5000, // 每5秒自动刷新
  });

  // 重跑
  const rerunMutation = useMutation({
    mutationFn: createRun,
    onSuccess: () => {
      message.success('已重新开始执行');
      queryClient.invalidateQueries({ queryKey: ['run-histories'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '重跑失败');
    },
  });

  const totalExecutions = historyData?.data?.data?.total || 0;
  const items = historyData?.data?.data?.items || [];

  // 计算统计数据
  const stats = {
    total: totalExecutions,
    passed: items.filter((i: Execution) => i.result === 'pass').length,
    failed: items.filter((i: Execution) => i.result === 'fail').length,
    running: items.filter((i: Execution) => i.result === 'running').length,
  };

  const passRate = stats.total > 0 ? Math.round((stats.passed / stats.total) * 100) : 0;

  const handleRerun = (record: Execution) => {
    // 使用createRun重新执行
    rerunMutation.mutate({
      type: record.type as 'testcase' | 'suite',
      target_ids: [record.target_id],
      device_serial: record.device_serial,
    });
  };

  const handleViewReport = (record: Execution) => {
    setSelectedTask(record);
    setReportVisible(true);
  };

  const handleViewLogs = (record: Execution) => {
    setCurrentTaskId(record.task_id);
    setLogsModalVisible(true);
  };

  const handleExportReport = async (record: Execution) => {
    try {
      // 调用导出 API
      const response = await fetch(`/api/v1/runs/${record.task_id}/export/html`);

      if (!response.ok) {
        throw new Error('导出失败');
      }

      // 获取 HTML 内容
      const htmlContent = await response.text();

      // 创建 Blob 对象
      const blob = new Blob([htmlContent], { type: 'text/html' });

      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `report_${record.task_id}.html`;

      // 触发下载
      document.body.appendChild(link);
      link.click();

      // 清理
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success('报告导出成功');
    } catch (error) {
      console.error('导出报告失败:', error);
      message.error('导出报告失败');
    }
  };

  // 使用 WebSocket 接收实时日志
  const { logs, isConnected, clearLogs } = useTaskLogs({
    taskId: currentTaskId || '',
    enabled: logsModalVisible && currentTaskId !== null,
    onLog: (log: TaskLog) => {
      // 可以在这里处理日志，例如滚动到底部
      if (log.testcase_result) {
        // 更新进度
        console.log('用例执行结果:', log.testcase_name, log.testcase_result);
      }
    },
    onComplete: () => {
      // 任务完成后的处理
      message.info('任务执行完成');
      // 刷新列表
      queryClient.invalidateQueries({ queryKey: ['run-histories'] });
    },
  });

  // 从日志中提取执行进度
  const getExecutionProgress = () => {
    const testcaseLogs = logs.filter(log => log.testcase_id);
    const totalTestcases = testcaseLogs.length > 0
      ? Math.max(...testcaseLogs.map(log => log.testcase_total || 0))
      : 0;
    const completedTestcases = testcaseLogs.filter(log =>
      log.testcase_result && log.testcase_result !== 'running'
    ).length;

    return {
      total: totalTestcases,
      completed: completedTestcases,
      percentage: totalTestcases > 0 ? Math.round((completedTestcases / totalTestcases) * 100) : 0,
      currentLog: logs.length > 0 ? logs[logs.length - 1] : null,
    };
  };

  const progress = getExecutionProgress();

  const getStatusTag = (result: string) => {
    switch (result) {
      case 'pass':
        return <Tag icon={<CheckCircleOutlined />} color="success">✓ 通过</Tag>;
      case 'fail':
        return <Tag icon={<CloseCircleOutlined />} color="error">✗ 失败</Tag>;
      case 'running':
        return <Tag icon={<ClockCircleOutlined />} color="processing">● 执行中</Tag>;
      case 'skipped':
        return <Tag icon={<MinusCircleOutlined />} color="default">— 跳过</Tag>;
      case 'error':
        return <Tag icon={<CloseCircleOutlined />} color="error">! 错误</Tag>;
      default:
        return <Tag color="default">{result}</Tag>;
    }
  };

  const formatDuration = (duration?: number) => {
    if (!duration) return '-';
    const seconds = Math.floor(duration / 1000);
    if (seconds < 60) return `${seconds}秒`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 180,
      render: (date: string) => date ? new Date(date).toLocaleString() : '-',
    },
    {
      title: '名称',
      dataIndex: 'target_name',
      key: 'target_name',
      render: (name: string, record: Execution) => (
        <Space>
          <strong>{name}</strong>
          <Tag color={record.type === 'testcase' ? 'blue' : 'purple'}>
            {record.type === 'testcase' ? '用例' : '套件'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      render: (result: string) => getStatusTag(result),
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration: number) => formatDuration(duration),
    },
    {
      title: '设备',
      dataIndex: 'device_serial',
      key: 'device_serial',
      render: (serial: string) => serial ? (
        <Tooltip title={serial}>
          <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
            {serial.length > 15 ? `${serial.substring(0, 15)}...` : serial}
          </span>
        </Tooltip>
      ) : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_: any, record: Execution) => (
        <Space size={4}>
          {record.type === 'suite' && (
            <Tooltip title="查看报告">
              <Button
                type="link"
                size="small"
                icon={<FileTextOutlined />}
                onClick={() => handleViewReport(record)}
              />
            </Tooltip>
          )}
          {record.result === 'running' && (
            <Tooltip title="查看实时日志">
              <Button
                type="link"
                size="small"
                icon={<EyeOutlined />}
                onClick={() => handleViewLogs(record)}
              />
            </Tooltip>
          )}
          <Tooltip title="导出报告">
            <Button
              type="link"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleExportReport(record)}
            />
          </Tooltip>
          <Tooltip title="重跑">
            <Button
              type="link"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleRerun(record)}
              loading={rerunMutation.isPending}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <span>执行历史</span>
            <span style={{ color: '#8c8c8c', fontSize: '14px' }}>最近 {totalExecutions} 条</span>
          </Space>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['run-histories'] })}
          >
            刷新
          </Button>
        }
      >
        {/* 统计卡片区 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="执行总次数"
                value={stats.total}
                styles={{ content: { color: '#1890ff' } }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="通过数"
                value={stats.passed}
                styles={{ content: { color: '#52c41a' } }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="失败数"
                value={stats.failed}
                styles={{ content: { color: '#ff4d4f' } }}
                prefix={<CloseCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="通过率"
                value={passRate}
                suffix="%"
                styles={{
                  content: {
                    color: passRate >= 80 ? '#52c41a' : passRate >= 60 ? '#faad14' : '#ff4d4f',
                  },
                }}
              />
              <Progress
                percent={passRate}
                strokeColor={{
                  '0%': '#ff4d4f',
                  '60%': '#faad14',
                  '80%': '#52c41a',
                }}
                showInfo={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>

        {/* 筛选栏 */}
        <Space style={{ marginBottom: '16px' }} size="middle" wrap>
          <DrawerSelector
            placeholder="执行状态"
            options={[
              { value: 'pass', label: '通过' },
              { value: 'fail', label: '失败' },
              { value: 'running', label: '执行中' },
              { value: 'stopped', label: '已停止' },
              { value: 'timeout', label: '超时' },
            ]}
            value={selectedStatus}
            onChange={setSelectedStatus}
            drawerWidth={320}
            placement="right"
          />
        </Space>

        <Table
          columns={columns}
          dataSource={items}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1400 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: totalExecutions,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (newPage, newPageSize) => {
              setPage(newPage);
              setPageSize(newPageSize || 20);
            },
          }}
        />
      </Card>

      {/* 实时日志弹窗 */}
      <Modal
        title={`实时日志 - ${currentTaskId || ''}`}
        open={logsModalVisible}
        onCancel={() => {
          setLogsModalVisible(false);
          setCurrentTaskId(null);
          clearLogs();
        }}
        footer={[
          <Button key="close" onClick={() => setLogsModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {/* 执行进度 */}
        {progress.total > 0 && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <div style={{ marginBottom: 8 }}>
              <span>执行进度: </span>
              <span style={{ marginLeft: 8, fontWeight: 'bold' }}>
                {progress.completed} / {progress.total} 用例
              </span>
              <span style={{ marginLeft: 16 }}>
                {progress.percentage}%
              </span>
            </div>
            <Progress
              percent={progress.percentage}
              status={progress.completed === progress.total ? 'success' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            {progress.currentLog && (
              <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
                当前: {progress.currentLog.message}
              </div>
            )}
          </Card>
        )}

        <div style={{ marginBottom: 8 }}>
          <Tag color={isConnected ? 'green' : 'red'}>
            {isConnected ? '已连接' : '未连接'}
          </Tag>
          <span style={{ marginLeft: 8 }}>
            共 {logs.length} 条日志
          </span>
        </div>

        <div
          style={{
            height: 400,
            overflowY: 'auto',
            backgroundColor: '#1e1e1e',
            padding: 16,
            borderRadius: 4,
            fontFamily: 'monospace',
            fontSize: 12,
          }}
        >
          {logs.length === 0 ? (
            <Empty description={isConnected ? '等待日志...' : '未连接'} />
          ) : (
            <List
              dataSource={logs}
              renderItem={(log, index) => {
                const logColor = {
                  'ERROR': '#ff4d4f',
                  'WARNING': '#faad14',
                  'INFO': '#1890ff',
                  'DEBUG': '#8c8c8c',
                  'SUCCESS': '#52c41a',
                }[log.level] || '#ffffff';

                return (
                  <div
                    key={index}
                    style={{
                      marginBottom: 4,
                      color: logColor,
                      wordBreak: 'break-all',
                    }}
                  >
                    <span style={{ color: '#8c8c8c', marginRight: 8 }}>
                      [{log.level}]
                    </span>
                    {log.testcase_name && (
                      <span style={{ color: '#faad14', marginRight: 8 }}>
                        [{log.testcase_name}]
                      </span>
                    )}
                    {log.message}
                  </div>
                );
              }}
            />
          )}
        </div>
      </Modal>

      {/* 套件报告 */}
      {selectedTask && (
        <SuiteReport
          visible={reportVisible}
          taskId={selectedTask.task_id}
          suiteName={selectedTask.target_name}
          onClose={() => {
            setReportVisible(false);
            setSelectedTask(null);
          }}
        />
      )}
    </div>
  );
};

export default History;
