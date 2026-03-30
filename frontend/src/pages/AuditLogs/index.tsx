import React, { useState } from 'react';
import {
  Card,
  Table,
  Tag,
  Space,
  Select,
  Input,
  Button,
  DatePicker,
  Drawer,
  Typography,
  Descriptions,
} from 'antd';
import { SearchOutlined, FileTextOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { getAuditLogs, type AuditLog, type AuditLogsQuery } from '../../services/permissions';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Text, Paragraph } = Typography;

const ACTION_COLORS: Record<string, string> = {
  user_login: 'green',
  user_logout: 'default',
  user_register: 'blue',
  project_create: 'cyan',
  project_update: 'blue',
  project_delete: 'red',
  element_create: 'cyan',
  element_update: 'blue',
  element_delete: 'red',
  step_create: 'cyan',
  step_update: 'blue',
  step_delete: 'red',
  flow_create: 'cyan',
  flow_update: 'blue',
  flow_delete: 'red',
  testcase_create: 'cyan',
  testcase_update: 'blue',
  testcase_delete: 'red',
  testcase_execute: 'purple',
  member_add: 'green',
  member_remove: 'orange',
  member_role_update: 'blue',
};

const ACTION_LABELS: Record<string, string> = {
  user_login: '用户登录',
  user_logout: '用户登出',
  user_register: '用户注册',
  project_create: '创建项目',
  project_update: '更新项目',
  project_delete: '删除项目',
  element_create: '创建元素',
  element_update: '更新元素',
  element_delete: '删除元素',
  step_create: '创建步骤',
  step_update: '更新步骤',
  step_delete: '删除步骤',
  flow_create: '创建流程',
  flow_update: '更新流程',
  flow_delete: '删除流程',
  testcase_create: '创建测试用例',
  testcase_update: '更新测试用例',
  testcase_delete: '删除测试用例',
  testcase_execute: '执行测试用例',
  member_add: '添加成员',
  member_remove: '移除成员',
  member_role_update: '更新成员角色',
};

const AuditLogsPage: React.FC = () => {
  const [query, setQuery] = useState<AuditLogsQuery>({ page: 1, page_size: 20 });
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // 获取审计日志
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['auditLogs', query],
    queryFn: () => getAuditLogs(query),
  });

  const logs = data?.items || [];
  const total = data?.total || 0;

  const handleSearch = (filters: Record<string, unknown>) => {
    setQuery({
      ...query,
      page: 1,
      ...filters,
    });
  };

  const handleTableChange = (pagination: any) => {
    setQuery({
      ...query,
      page: pagination.current,
      page_size: pagination.pageSize,
    });
  };

  const showLogDetail = (log: AuditLog) => {
    setSelectedLog(log);
    setIsDrawerOpen(true);
  };

  const columns = [
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string | null) => (date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-'),
      sorter: true,
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (username: string | null) => <strong>{username || '-'}</strong>,
    },
    {
      title: '操作类型',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action: string) => (
        <Tag color={ACTION_COLORS[action] || 'default'}>{ACTION_LABELS[action] || action}</Tag>
      ),
    },
    {
      title: '资源',
      key: 'resource',
      width: 200,
      render: (_: unknown, record: AuditLog) => (
        <Space direction="vertical" size={0}>
          <Text type="secondary">{record.resource_type || '-'}</Text>
          {record.resource_id && <Text>{`ID: ${record.resource_id}`}</Text>}
        </Space>
      ),
    },
    {
      title: '项目ID',
      dataIndex: 'project_id',
      key: 'project_id',
      width: 100,
      render: (projectId: number | null) => (projectId ? <Tag>{projectId}</Tag> : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status === 'success' ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (ip: string | null) => ip || '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: unknown, record: AuditLog) => (
        <Button
          type="link"
          size="small"
          icon={<FileTextOutlined />}
          onClick={() => showLogDetail(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>操作审计日志</span>
          </Space>
        }
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        }
      >
        <Space style={{ marginBottom: 16 }} size="middle">
          <Input.Search
            placeholder="搜索操作类型"
            style={{ width: 200 }}
            onSearch={(value) => handleSearch({ action: value || undefined })}
            enterButton
          />
          <Input.Search
            placeholder="资源类型"
            style={{ width: 200 }}
            onSearch={(value) => handleSearch({ resource_type: value || undefined })}
            enterButton
          />
          <Input.Search
            placeholder="项目ID"
            style={{ width: 150 }}
            type="number"
            onSearch={(value) => handleSearch({ project_id: value ? Number(value) : undefined })}
            enterButton
          />
        </Space>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: query.page,
            pageSize: query.page_size,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条记录`,
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Drawer
        title="操作详情"
        placement="right"
        width={600}
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      >
        {selectedLog && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Descriptions bordered column={1}>
              <Descriptions.Item label="操作时间">
                {selectedLog.created_at
                  ? dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="操作用户">
                {selectedLog.username || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="用户ID">
                {selectedLog.user_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="操作类型">
                <Tag color={ACTION_COLORS[selectedLog.action] || 'default'}>
                  {ACTION_LABELS[selectedLog.action] || selectedLog.action}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="资源类型">
                {selectedLog.resource_type || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="资源ID">
                {selectedLog.resource_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="项目ID">
                {selectedLog.project_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="IP地址">
                {selectedLog.ip_address || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={selectedLog.status === 'success' ? 'green' : 'red'}>
                  {selectedLog.status === 'success' ? '成功' : '失败'}
                </Tag>
              </Descriptions.Item>
              {selectedLog.error_message && (
                <Descriptions.Item label="错误信息">
                  <Text type="danger">{selectedLog.error_message}</Text>
                </Descriptions.Item>
              )}
            </Descriptions>

            {selectedLog.details && (
              <div>
                <Typography.Title level={5}>操作详情</Typography.Title>
                <pre
                  style={{
                    background: '#f5f5f5',
                    padding: 12,
                    borderRadius: 4,
                    overflow: 'auto',
                    maxHeight: 400,
                  }}
                >
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            )}
          </Space>
        )}
      </Drawer>
    </div>
  );
};

export default AuditLogsPage;
