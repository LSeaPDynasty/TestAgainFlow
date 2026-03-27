import React, { useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Input,
  Modal,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  CopyOutlined,
  DownloadOutlined,
  EyeOutlined,
  FileTextOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { getRunHistories, type RunHistory } from '../../services/run';
import { getRunLogs } from '../../services/runLog';
import DrawerSelector from '../../components/DrawerSelector';

const { Text } = Typography;

type LogLevel = 'ALL' | 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
type RunResult = 'pending' | 'running' | 'pass' | 'fail' | 'stopped' | 'timeout';

type LogItem = {
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR' | string;
  message: string;
  created_at: string;
};

type ReportModalState = {
  open: boolean;
  loading: boolean;
  taskId: string;
  taskName: string;
  html: string;
  statistics: any;
  logs: any[];
};

const statusConfig: Record<RunResult, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  running: { color: 'processing', text: '执行中' },
  pass: { color: 'success', text: '成功' },
  fail: { color: 'error', text: '失败' },
  stopped: { color: 'warning', text: '已停止' },
  timeout: { color: 'warning', text: '超时' },
};

const levelColorMap: Record<string, string> = {
  ERROR: '#ff4d4f',
  WARNING: '#faad14',
  SUCCESS: '#52c41a',
  INFO: '#1890ff',
};

const RunsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedStatus, setSelectedStatus] = useState<RunResult | undefined>();
  const [searchText, setSearchText] = useState('');

  const [logModal, setLogModal] = useState({
    open: false,
    taskId: '',
    taskName: '',
  });
  const [logLevel, setLogLevel] = useState<LogLevel>('ALL');
  const [logSearch, setLogSearch] = useState('');

  const [reportModal, setReportModal] = useState<ReportModalState>({
    open: false,
    loading: false,
    taskId: '',
    taskName: '',
    html: '',
    statistics: null,
    logs: [],
  });

  const { data: runsResp, isLoading: runsLoading, refetch } = useQuery({
    queryKey: ['run-histories', page, pageSize, selectedStatus],
    queryFn: () =>
      getRunHistories({
        page,
        page_size: pageSize,
        status: selectedStatus,
      }),
  });

  const { data: logsResp, isLoading: logsLoading } = useQuery({
    queryKey: ['run-logs', logModal.taskId],
    queryFn: () => getRunLogs(logModal.taskId),
    enabled: logModal.open && !!logModal.taskId,
  });

  const serverItems: RunHistory[] = runsResp?.data?.data?.items || [];
  const total = runsResp?.data?.data?.total || 0;
  const logs: LogItem[] = logsResp?.data?.data || [];

  const items = useMemo(() => {
    const keyword = searchText.trim().toLowerCase();
    if (!keyword) {
      return serverItems;
    }
    return serverItems.filter((row) => {
      const target = String(row.target_name || '').toLowerCase();
      const task = String(row.task_id || '').toLowerCase();
      const device = String(row.device_serial || '').toLowerCase();
      return target.includes(keyword) || task.includes(keyword) || device.includes(keyword);
    });
  }, [serverItems, searchText]);

  const stats = useMemo(() => {
    const totalCount = items.length;
    const passed = items.filter((x) => x.result === 'pass').length;
    const failed = items.filter((x) => x.result === 'fail').length;
    const running = items.filter((x) => x.result === 'running').length;
    const passRate = totalCount > 0 ? Math.round((passed / totalCount) * 100) : 0;
    return { totalCount, passed, failed, running, passRate };
  }, [items]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (logLevel !== 'ALL' && log.level !== logLevel) {
        return false;
      }
      if (logSearch && !String(log.message || '').toLowerCase().includes(logSearch.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [logs, logLevel, logSearch]);

  const logStats = useMemo(() => {
    return logs.reduce(
      (acc, cur) => {
        acc.total += 1;
        if (cur.level === 'ERROR') acc.ERROR += 1;
        if (cur.level === 'WARNING') acc.WARNING += 1;
        if (cur.level === 'SUCCESS') acc.SUCCESS += 1;
        if (cur.level === 'INFO') acc.INFO += 1;
        return acc;
      },
      { total: 0, ERROR: 0, WARNING: 0, SUCCESS: 0, INFO: 0 },
    );
  }, [logs]);

  function copyLogs() {
    const text = logs
      .map((log) => `[${new Date(log.created_at).toLocaleTimeString()}] [${log.level}] ${log.message}`)
      .join('\n');
    navigator.clipboard.writeText(text).then(() => {
      message.success('日志已复制到剪贴板');
    });
  }

  async function handleExportReport(record: RunHistory) {
    try {
      const response = await fetch(`/api/v1/runs/${record.task_id}/export/zip`);
      if (!response.ok) {
        throw new Error('export failed');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `report_${record.task_id}.zip`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      message.success('报告导出成功');
    } catch {
      message.error('报告导出失败');
    }
  }

  async function handleViewReport(record: RunHistory) {
    setReportModal({
      open: true,
      loading: true,
      taskId: record.task_id,
      taskName: record.target_name || record.task_id,
      html: '',
      statistics: null,
      logs: [],
    });

    try {
      const response = await fetch(`/api/v1/runs/${record.task_id}/export/html`);
      const json = await response.json();
      if (json?.code !== 0) {
        throw new Error('invalid response');
      }
      setReportModal({
        open: true,
        loading: false,
        taskId: record.task_id,
        taskName: record.target_name || record.task_id,
        html: json?.data?.html || '',
        statistics: json?.data?.statistics || null,
        logs: json?.data?.logs || [],
      });
    } catch {
      setReportModal((prev) => ({ ...prev, loading: false }));
      message.error('获取报告失败');
    }
  }

  const columns: ColumnsType<RunHistory> = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      width: 220,
      render: (v: string) => <Text code>{v}</Text>,
    },
    {
      title: '类型',
      dataIndex: 'type',
      width: 100,
      render: (v: string) => {
        const typeConfig: Record<string, { color: string; text: string }> = {
          'testcase': { color: 'blue', text: '用例' },
          'suite': { color: 'purple', text: '套件' },
          'test_plan': { color: 'green', text: '测试计划' },
        };
        const config = typeConfig[v] || { color: 'default', text: v };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '目标',
      dataIndex: 'target_name',
      ellipsis: true,
    },
    {
      title: '设备',
      dataIndex: 'device_serial',
      width: 170,
      render: (v: string) => <Text code>{v || '未指定'}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'result',
      width: 100,
      render: (v: RunResult) => <Tag color={statusConfig[v]?.color || 'default'}>{statusConfig[v]?.text || v}</Tag>,
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      width: 180,
      render: (v: string) => {
        if (!v) return '-';
        // 后端返回的是 UTC 时间，需要转换为本地时间
        const date = new Date(v + 'Z'); // 添加 'Z' 表示 UTC 时间
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        });
      },
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      width: 100,
      render: (v?: number) => (v ? `${v.toFixed(2)}s` : '-'),
    },
    {
      title: '操作',
      width: 220,
      fixed: 'right',
      render: (_: any, row: RunHistory) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() =>
              setLogModal({
                open: true,
                taskId: row.task_id,
                taskName: row.target_name || row.task_id,
              })
            }
          >
            日志
          </Button>
          <Button type="link" size="small" icon={<FileTextOutlined />} onClick={() => handleViewReport(row)}>
            报告
          </Button>
          <Button type="link" size="small" icon={<DownloadOutlined />} onClick={() => handleExportReport(row)}>
            导出
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={`执行历史（共 ${total} 条）`}
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={runsLoading}>
            刷新
          </Button>
        }
      >
        <Row gutter={12} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic title="本页任务数" value={stats.totalCount} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="成功" value={stats.passed} valueStyle={{ color: '#52c41a' }} prefix={<CheckCircleOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="失败" value={stats.failed} valueStyle={{ color: '#ff4d4f' }} prefix={<CloseCircleOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="通过率" value={stats.passRate} suffix="%" />
              <Progress percent={stats.passRate} showInfo={false} size="small" />
            </Card>
          </Col>
        </Row>

        <Space style={{ marginBottom: 16 }} wrap>
          <DrawerSelector
            placeholder="按状态筛选"
            options={[
              { label: '成功', value: 'pass' },
              { label: '失败', value: 'fail' },
              { label: '执行中', value: 'running' },
              { label: '已停止', value: 'stopped' },
              { label: '超时', value: 'timeout' },
            ]}
            value={selectedStatus}
            onChange={(v) => {
              setSelectedStatus(v);
              setPage(1);
            }}
            drawerWidth={320}
            placement="right"
          />

          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="搜索目标/任务ID/设备（当前页）"
            style={{ width: 320 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </Space>

        <Table<RunHistory>
          rowKey="task_id"
          loading={runsLoading}
          dataSource={items}
          columns={columns}
          scroll={{ x: 1300 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            onChange: (nextPage, nextPageSize) => {
              setPage(nextPage);
              setPageSize(nextPageSize || 20);
            },
          }}
        />
      </Card>

      <Modal
        title={
          <Space>
            <FileTextOutlined />
            <span>执行日志 - {logModal.taskName}</span>
            <Tag color="blue">{logModal.taskId}</Tag>
          </Space>
        }
        open={logModal.open}
        onCancel={() => {
          setLogModal({ open: false, taskId: '', taskName: '' });
          setLogLevel('ALL');
          setLogSearch('');
        }}
        footer={null}
        width={1150}
      >
        <Spin spinning={logsLoading}>
          {logs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 32, color: '#8c8c8c' }}>暂无日志</div>
          ) : (
            <div>
              <Card size="small" style={{ marginBottom: 12 }}>
                <Space wrap>
                  <Tag>总计: {logStats.total}</Tag>
                  <Tag color="red">错误: {logStats.ERROR}</Tag>
                  <Tag color="orange">警告: {logStats.WARNING}</Tag>
                  <Tag color="green">成功: {logStats.SUCCESS}</Tag>
                  <Tag color="blue">信息: {logStats.INFO}</Tag>
                  <Button size="small" icon={<CopyOutlined />} onClick={copyLogs}>
                    复制全部
                  </Button>
                </Space>
                <Space style={{ marginTop: 10 }}>
                  <DrawerSelector
                    placeholder="日志级别"
                    options={[
                      { label: '全部', value: 'ALL' },
                      { label: '错误', value: 'ERROR' },
                      { label: '警告', value: 'WARNING' },
                      { label: '成功', value: 'SUCCESS' },
                      { label: '信息', value: 'INFO' },
                    ]}
                    value={logLevel}
                    onChange={setLogLevel}
                    drawerWidth={280}
                    placement="right"
                  />
                  <Input
                    allowClear
                    size="small"
                    style={{ width: 320 }}
                    placeholder="搜索日志内容"
                    value={logSearch}
                    onChange={(e) => setLogSearch(e.target.value)}
                  />
                  <Text type="secondary">
                    显示 {filteredLogs.length} / {logs.length}
                  </Text>
                </Space>
              </Card>

              <div
                style={{
                  maxHeight: 560,
                  overflowY: 'auto',
                  padding: 14,
                  borderRadius: 6,
                  backgroundColor: '#1f1f1f',
                  fontFamily: 'Consolas, Monaco, monospace',
                  fontSize: 13,
                }}
              >
                {filteredLogs.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 32, color: '#8c8c8c' }}>没有符合条件的日志</div>
                ) : (
                  filteredLogs.map((log, idx) => {
                    const color = levelColorMap[log.level] || '#d4d4d4';
                    // 正确处理 UTC 时间
                    const logTime = log.created_at ? new Date(log.created_at + 'Z') : new Date();
                    return (
                      <div key={idx} style={{ marginBottom: 4, lineHeight: 1.6, wordBreak: 'break-all' }}>
                        <span style={{ color: '#8c8c8c', marginRight: 8 }}>
                          [{logTime.toLocaleTimeString('zh-CN', { hour12: false })}]
                        </span>
                        <span
                          style={{
                            color,
                            padding: '1px 6px',
                            borderRadius: 4,
                            marginRight: 8,
                            background: `${color}20`,
                            fontWeight: 600,
                          }}
                        >
                          [{log.level}]
                        </span>
                        <span style={{ color: '#e8e8e8' }}>{log.message}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </Spin>
      </Modal>

      <Modal
        title={
          <Space>
            <FileTextOutlined />
            <span>测试报告 - {reportModal.taskName}</span>
            <Tag color="blue">{reportModal.taskId}</Tag>
          </Space>
        }
        open={reportModal.open}
        onCancel={() => setReportModal((prev) => ({ ...prev, open: false }))}
        footer={[
          <Button key="close" onClick={() => setReportModal((prev) => ({ ...prev, open: false }))}>
            关闭
          </Button>,
          <Button
            key="export"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => {
              const run = serverItems.find((x) => x.task_id === reportModal.taskId);
              if (run) handleExportReport(run);
            }}
          >
            导出 ZIP
          </Button>,
        ]}
        width={1150}
      >
        {reportModal.loading ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <Spin />
          </div>
        ) : (
          <Tabs
            items={[
              {
                key: 'preview',
                label: '报告预览',
                children: reportModal.html ? (
                  <div
                    style={{ maxHeight: '68vh', overflowY: 'auto', padding: 12, backgroundColor: '#f5f5f5' }}
                    dangerouslySetInnerHTML={{ __html: reportModal.html }}
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: 28, color: '#8c8c8c' }}>暂无报告内容</div>
                ),
              },
              {
                key: 'stats',
                label: '统计信息',
                children: reportModal.statistics ? (
                  <Row gutter={12}>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic title="总用例数" value={reportModal.statistics.total || 0} />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic title="成功" value={reportModal.statistics.success || 0} valueStyle={{ color: '#52c41a' }} />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic title="失败" value={reportModal.statistics.failed || 0} valueStyle={{ color: '#ff4d4f' }} />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic title="跳过" value={reportModal.statistics.skipped || 0} valueStyle={{ color: '#8c8c8c' }} />
                      </Card>
                    </Col>
                  </Row>
                ) : (
                  <div style={{ textAlign: 'center', padding: 28, color: '#8c8c8c' }}>暂无统计数据</div>
                ),
              },
              {
                key: 'logs',
                label: `执行日志 (${reportModal.logs.length})`,
                children:
                  reportModal.logs.length > 0 ? (
                    <div
                      style={{
                        maxHeight: 520,
                        overflowY: 'auto',
                        padding: 14,
                        backgroundColor: '#1f1f1f',
                        borderRadius: 6,
                        fontFamily: 'Consolas, Monaco, monospace',
                        fontSize: 13,
                      }}
                    >
                      {reportModal.logs.map((log: any, idx: number) => {
                        const color = levelColorMap[log.level] || '#d4d4d4';
                        return (
                          <div key={idx} style={{ marginBottom: 4, lineHeight: 1.6, wordBreak: 'break-all' }}>
                            <span style={{ color: '#8c8c8c', marginRight: 8 }}>[{log.timestamp}]</span>
                            <span style={{ color, fontWeight: 600, marginRight: 8 }}>[{log.level}]</span>
                            <span style={{ color: '#e8e8e8' }}>{log.message}</span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 28, color: '#8c8c8c' }}>暂无日志</div>
                  ),
              },
            ]}
          />
        )}
      </Modal>
    </div>
  );
};

export default RunsPage;
