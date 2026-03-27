import React, { useState } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Modal,
  Form,
  message,
  Popconfirm,
  Tooltip,
  Switch,
  InputNumber,
  Row,
  Col,
  Radio,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  StopOutlined,
  SearchOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getScheduledJobs,
  createScheduledJob,
  updateScheduledJob,
  deleteScheduledJob,
  runScheduledJob,
  toggleScheduledJob,
  type ScheduledJob,
  type ScheduledJobCreate,
} from '../../services/scheduledJob';
import { getTestcases } from '../../services/testcase';
import { getSuites } from '../../services/suite';
import { getDevices } from '../../services/device';
import { useProject } from '../../contexts/ProjectContext';

const { Search } = Input;
const { Option } = Select;
const { TextArea } = Input;

// 任务状态配置
const STATUS_CONFIG = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
  running: { color: 'processing', icon: <ReloadOutlined spin />, text: '运行中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  disabled: { color: 'default', icon: <StopOutlined />, text: '已禁用' },
};

const ScheduledJobs: React.FC = () => {
  const { selectedProjectId } = useProject();
  const [searchText, setSearchText] = useState('');
  const [enabledOnly, setEnabledOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingJob, setEditingJob] = useState<ScheduledJob | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [runModalVisible, setRunModalVisible] = useState(false);
  const [selectedJob, setSelectedJob] = useState<ScheduledJob | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [form] = Form.useForm();

  const queryClient = useQueryClient();

  // 获取定时任务列表
  const { data: jobsData, isLoading } = useQuery({
    queryKey: ['scheduled-jobs', page, pageSize, enabledOnly, selectedProjectId],
    queryFn: () =>
      getScheduledJobs({
        page,
        page_size: pageSize,
        enabled_only: enabledOnly,
        project_id: selectedProjectId || undefined,
      }),
  });

  // 获取测试用例列表
  const { data: testcasesData } = useQuery({
    queryKey: ['testcases-list'],
    queryFn: () => getTestcases({ page: 1, page_size: 1000, project_id: selectedProjectId || undefined }),
  });

  // 获取套件列表
  const { data: suitesData } = useQuery({
    queryKey: ['suites-list'],
    queryFn: () => getSuites({ page: 1, page_size: 1000, project_id: selectedProjectId || undefined }),
  });

  // 获取设备列表
  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: () => getDevices({ page: 1, page_size: 100 }),
  });

  const testcasesList = testcasesData?.data?.data?.items || [];
  const suitesList = suitesData?.data?.data?.items || [];
  const devicesList = devicesData?.data?.data?.items || [];

  // 创建任务
  const createMutation = useMutation({
    mutationFn: createScheduledJob,
    onSuccess: () => {
      message.success('创建成功');
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // 更新任务
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateScheduledJob(id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 删除任务
  const deleteMutation = useMutation({
    mutationFn: deleteScheduledJob,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 运行任务
  const runMutation = useMutation({
    mutationFn: ({ jobId, deviceSerial }: { jobId: number; deviceSerial: string }) =>
      runScheduledJob(jobId, deviceSerial),
    onSuccess: (response) => {
      const taskId = response.data.data.task_id;
      message.success(`定时任务已开始执行，任务ID: ${taskId}`);
      setRunModalVisible(false);
      setSelectedDevice('');
      // 跳转到执行历史页面
      setTimeout(() => {
        window.location.href = '/#/runs';
      }, 500);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '启动执行失败');
    },
  });

  // 切换启用状态
  const toggleMutation = useMutation({
    mutationFn: toggleScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '操作失败');
    },
  });

  const totalJobs = jobsData?.data?.data?.total || 0;
  const items = jobsData?.data?.data?.items || [];

  const handleModalOpen = (job?: ScheduledJob) => {
    if (job) {
      setEditingJob(job);
      form.setFieldsValue({
        name: job.name,
        description: job.description,
        job_type: job.job_type,
        target_id: job.target_id,
        cron_expression: job.cron_expression,
        device_serial: job.device_serial,
        enabled: job.enabled,
      });
    } else {
      setEditingJob(null);
      form.resetFields();
      form.setFieldsValue({
        job_type: 'testcase',
        enabled: true,
      });
    }
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingJob(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (editingJob) {
        updateMutation.mutate({ id: editingJob.id, data: values });
      } else {
        createMutation.mutate(values);
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const handleRun = (job: ScheduledJob) => {
    setSelectedJob(job);
    setRunModalVisible(true);
  };

  const handleToggleEnabled = (job: ScheduledJob) => {
    toggleMutation.mutate(job.id);
  };

  const handleConfirmRun = () => {
    if (!selectedDevice) {
      message.warning('请选择设备');
      return;
    }
    if (selectedJob) {
      runMutation.mutate({
        jobId: selectedJob.id,
        deviceSerial: selectedDevice,
      });
    }
  };

  // Cron表达式示例
  const cronExamples = [
    { label: '每分钟', value: '* * * * *', desc: '每分钟执行一次' },
    { label: '每小时', value: '0 * * * *', desc: '每小时的第0分钟执行' },
    { label: '每天9点', value: '0 9 * * *', desc: '每天早上9点执行' },
    { label: '每周一9点', value: '0 9 * * 1', desc: '每周一早上9点执行' },
    { label: '每月1号0点', value: '0 0 1 * *', desc: '每月1号凌晨执行' },
  ];

  const columns = [
    {
      title: '序号',
      key: 'index',
      width: 80,
      render: (_: any, __: any, index: number) => (
        <span style={{ color: '#8c8c8c', fontFamily: 'monospace' }}>
          {(index + 1).toString().padStart(2, '0')}
        </span>
      ),
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <strong>{name}</strong>,
    },
    {
      title: '类型',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'testcase' ? 'blue' : 'purple'}>
          {type === 'testcase' ? '用例' : '套件'}
        </Tag>
      ),
    },
    {
      title: '目标',
      dataIndex: 'target_name',
      key: 'target_name',
      ellipsis: true,
      render: (name: string) => name || '-',
    },
    {
      title: 'Cron表达式',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      width: 150,
      render: (cron: string) => (
        <Tooltip title={cron}>
          <code style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '2px 6px', borderRadius: '3px' }}>
            {cron}
          </code>
        </Tooltip>
      ),
    },
    {
      title: '设备',
      dataIndex: 'device_serial',
      key: 'device_serial',
      width: 120,
      render: (serial: string) => serial || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: keyof typeof STATUS_CONFIG, record: ScheduledJob) => {
        const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
        return (
          <Tag color={config.color} icon={config.icon} style={{ cursor: 'help' }}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '启用',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record: ScheduledJob) => (
        <Switch
          checked={enabled}
          onChange={() => handleToggleEnabled(record)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          size="small"
        />
      ),
    },
    {
      title: '上次运行',
      dataIndex: 'last_run_time',
      key: 'last_run_time',
      width: 160,
      render: (time: string) => (time ? new Date(time).toLocaleString() : '-'),
    },
    {
      title: '上次状态',
      dataIndex: 'last_run_status',
      key: 'last_run_status',
      width: 100,
      render: (status: string, record: ScheduledJob) => {
        if (!status) return '-';
        const color = status === 'success' ? 'success' : 'error';
        return <Tag color={color}>{status === 'success' ? '成功' : '失败'}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: ScheduledJob) => (
        <Space size="small">
          <Tooltip title="立即执行">
            <Button
              type="text"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleRun(record)}
              disabled={!record.enabled}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleModalOpen(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description={`确定要删除定时任务 "${record.name}" 吗？此操作不可恢复。`}
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <span><CalendarOutlined /> 定时任务管理</span>
            <span style={{ color: '#8c8c8c', fontSize: '14px' }}>共 {totalJobs} 个任务</span>
          </Space>
        }
        extra={
          <Space>
            <Switch
              checked={enabledOnly}
              onChange={setEnabledOnly}
              checkedChildren="仅显示启用"
              size="small"
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={() => queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] })}
            >
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleModalOpen()}>
              新建任务
            </Button>
          </Space>
        }
      >
        {/* 筛选栏 */}
        <Space style={{ marginBottom: '16px' }} size="middle" wrap>
          <Search
            placeholder="搜索任务名称"
            allowClear
            style={{ width: 240 }}
            onSearch={setSearchText}
            enterButton={<SearchOutlined />}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] })}
          >
            刷新
          </Button>
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
            total: totalJobs,
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

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingJob ? `编辑定时任务 · ${editingJob.name}` : '新建定时任务'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleModalClose}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="任务名称"
                name="name"
                rules={[{ required: true, message: '请输入任务名称' }]}
              >
                <Input placeholder="例如: 每日冒烟测试" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="任务类型"
                name="job_type"
                rules={[{ required: true, message: '请选择任务类型' }]}
              >
                <Radio.Group>
                  <Radio value="testcase">用例</Radio>
                  <Radio value="suite">套件</Radio>
                </Radio.Group>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="选择目标"
                name="target_id"
                rules={[{ required: true, message: '请选择目标' }]}
              >
                <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.job_type !== currentValues.job_type}>
                  <Select placeholder="请选择任务类型">
                    {form.getFieldValue('job_type') === 'testcase' ? (
                      testcasesList.map((tc: any) => (
                        <Option key={tc.id} value={tc.id}>
                          {tc.name}
                        </Option>
                      ))
                    ) : (
                      suitesList.map((suite: any) => (
                        <Option key={suite.id} value={suite.id}>
                          {suite.name}
                        </Option>
                      ))
                    )}
                  </Select>
                </Form.Item>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="执行设备"
                name="device_serial"
              >
                <Select placeholder="选择执行设备" allowClear>
                  {devicesList.map((device: any) => (
                    <Option key={device.serial} value={device.serial}>
                      {device.name || device.serial} ({device.status === 'online' ? '在线' : '离线'})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Cron表达式"
            name="cron_expression"
            rules={[{ required: true, message: '请输入Cron表达式' }]}
            tooltip="Cron表达式格式: 分 时 日 月 周 年"
          >
            <Input
              placeholder="例如: 0 9 * * * (每天早上9点)"
              addonAfter={
                <Select
                  style={{ width: 150 }}
                  placeholder="选择常用模板"
                  onChange={(value) => {
                    if (value) {
                      form.setFieldsValue({ cron_expression: value });
                    }
                  }}
                >
                  {cronExamples.map((example) => (
                    <Option key={example.value} value={example.value}>
                      {example.label} - {example.desc}
                    </Option>
                  ))}
                </Select>
              }
            />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="任务描述" />
          </Form.Item>

          <Form.Item
            label="启用状态"
            name="enabled"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <div style={{
            padding: '12px',
            backgroundColor: '#e6f7ff',
            border: '1px solid #91d5ff',
            borderRadius: '4px',
            color: '#0050b3',
            fontSize: '13px',
          }}>
            💡 <strong>Cron表达式说明：</strong><br />
            格式：分 时 日 月 周 年<br />
            示例：<code>0 9 * * *</code> = 每天早上9点<br />
            <code>0 */2 * *</code> = 每2小时<br />
            <code>0 9 * * 1</code> = 每周一早上9点
          </div>
        </Form>
      </Modal>

      {/* 执行任务弹窗 */}
      <Modal
        title={`执行任务 - ${selectedJob?.name || ''}`}
        open={runModalVisible}
        onOk={handleConfirmRun}
        onCancel={() => {
          setRunModalVisible(false);
          setSelectedDevice('');
        }}
        okText="开始执行"
        cancelText="取消"
        width={600}
      >
        <Form layout="vertical">
          <Form.Item label="选择设备" required>
            <Select
              placeholder="请选择要执行测试的设备"
              value={selectedDevice}
              onChange={setSelectedDevice}
            >
              {devicesList.map((device: any) => (
                <Option key={device.serial} value={device.serial}>
                  <Space>
                    <span>{device.name || device.serial}</span>
                    <Tag color={device.status === 'online' ? 'success' : 'error'}>
                      {device.status === 'online' ? '在线' : '离线'}
                    </Tag>
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>

          {selectedJob && (
            <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
              <p><strong>任务信息：</strong></p>
              <p>名称：{selectedJob.name}</p>
              <p>类型：{selectedJob.job_type === 'testcase' ? '用例' : '套件'}</p>
              <p>目标：{selectedJob.target_name}</p>
              <p>Cron：{selectedJob.cron_expression}</p>
            </div>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default ScheduledJobs;
