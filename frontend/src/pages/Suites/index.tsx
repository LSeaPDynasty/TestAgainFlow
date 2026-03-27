import React, { useMemo, useState } from 'react';
import {
  Button,
  Card,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Tooltip,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  CopyOutlined,
  PlayCircleOutlined,
  ThunderboltOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getSuites,
  getSuite,
  createSuite,
  updateSuite,
  deleteSuite,
  duplicateSuite,
  type Suite,
  type SuiteCreate,
} from '../../services/suite';
import { getTestcases } from '../../services/testcase';
import { createRun } from '../../services/run';
import { getDevices } from '../../services/device';
import { useProject } from '../../contexts/ProjectContext';

const { Search, TextArea } = Input;

type FormData = {
  name: string;
  description?: string;
  enabled: boolean;
};

const SuitesPage: React.FC = () => {
  const { selectedProjectId } = useProject();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<FormData>();

  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingSuite, setEditingSuite] = useState<Suite | null>(null);
  const [suiteTestcaseIds, setSuiteTestcaseIds] = useState<number[]>([]);
  const [addTestcaseId, setAddTestcaseId] = useState<number | undefined>();

  const [runModalOpen, setRunModalOpen] = useState(false);
  const [batchRunModalOpen, setBatchRunModalOpen] = useState(false);
  const [selectedSuite, setSelectedSuite] = useState<Suite | null>(null);
  const [deviceSerial, setDeviceSerial] = useState('');

  const { data: suitesResp, isLoading: suitesLoading } = useQuery({
    queryKey: ['suites', page, pageSize, searchText, selectedProjectId],
    queryFn: () =>
      getSuites({
        page,
        page_size: pageSize,
        search: searchText || undefined,
        include_stats: true,
        project_id: selectedProjectId || undefined,
      }),
  });

  const { data: testcasesResp, isLoading: testcasesLoading } = useQuery({
    queryKey: ['testcases-for-suites', selectedProjectId],
    queryFn: () =>
      getTestcases({
        page: 1,
        page_size: 1000,
        project_id: selectedProjectId || undefined,
      }),
    enabled: modalOpen,
  });

  const { data: devicesResp } = useQuery({
    queryKey: ['devices-for-suites-run'],
    queryFn: () => getDevices({ page: 1, page_size: 200 }),
    enabled: runModalOpen || batchRunModalOpen,
  });

  const suites: Suite[] = suitesResp?.data?.data?.items || [];
  const total = suitesResp?.data?.data?.total || 0;
  const testcases = testcasesResp?.data?.data?.items || [];
  const devices = devicesResp?.data?.data?.items || [];
  const testcaseMap = new Map<number, any>(testcases.map((x: any) => [x.id, x]));

  const deviceOptions = devices.map((d: any) => ({
    label: `${d.name || d.serial} (${d.status})`,
    value: d.serial,
    disabled: d.status !== 'online',
  }));

  const createMutation = useMutation({
    mutationFn: createSuite,
    onSuccess: () => {
      message.success('创建成功');
      closeEditModal();
      queryClient.invalidateQueries({ queryKey: ['suites'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<SuiteCreate> }) => updateSuite(id, data),
    onSuccess: () => {
      message.success('更新成功');
      closeEditModal();
      queryClient.invalidateQueries({ queryKey: ['suites'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSuite,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['suites'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '删除失败'),
  });

  const duplicateMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) => duplicateSuite(id, { new_name: name }),
    onSuccess: () => {
      message.success('复制成功');
      queryClient.invalidateQueries({ queryKey: ['suites'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '复制失败'),
  });

  const toggleEnabledMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) => updateSuite(id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['suites'] }),
    onError: (e: any) => message.error(e?.response?.data?.message || '状态更新失败'),
  });

  const executeMutation = useMutation({
    mutationFn: ({ suiteIds, serial }: { suiteIds: number[]; serial: string }) =>
      createRun({
        type: 'suite',
        target_ids: suiteIds,
        device_serial: serial,
      }),
    onSuccess: () => {
      message.success('执行任务已创建');
      setRunModalOpen(false);
      setBatchRunModalOpen(false);
      setSelectedSuite(null);
      setSelectedRowKeys([]);
      setDeviceSerial('');
      queryClient.invalidateQueries({ queryKey: ['run-histories'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '执行失败'),
  });

  function closeEditModal() {
    setModalOpen(false);
    setEditingSuite(null);
    setSuiteTestcaseIds([]);
    setAddTestcaseId(undefined);
    form.resetFields();
  }

  function normalizeTestcaseIds(rawTestcases: any[]) {
    return (rawTestcases || [])
      .map((item: any) => Number(item?.testcase_id ?? item?.id))
      .filter((x: number) => Number.isFinite(x) && x > 0);
  }

  async function openCreateModal() {
    setEditingSuite(null);
    setSuiteTestcaseIds([]);
    form.setFieldsValue({
      name: '',
      description: '',
      enabled: true,
    });
    setModalOpen(true);
  }

  async function openEditModal(suite: Suite) {
    setEditingSuite(suite);
    form.setFieldsValue({
      name: suite.name,
      description: suite.description || '',
      enabled: suite.enabled,
    });
    setModalOpen(true);
    try {
      const resp = await getSuite(suite.id);
      const detail = resp?.data?.data;
      setSuiteTestcaseIds(normalizeTestcaseIds(detail?.testcases || []));
    } catch {
      setSuiteTestcaseIds([]);
      message.warning('套件详情加载失败，已使用空用例列表');
    }
  }

  function moveTestcase(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= suiteTestcaseIds.length) {
      return;
    }
    const next = [...suiteTestcaseIds];
    [next[index], next[target]] = [next[target], next[index]];
    setSuiteTestcaseIds(next);
  }

  function removeTestcase(index: number) {
    setSuiteTestcaseIds((prev) => prev.filter((_, i) => i !== index));
  }

  function addTestcase() {
    if (!addTestcaseId) {
      message.warning('请先选择用例');
      return;
    }
    if (suiteTestcaseIds.includes(addTestcaseId)) {
      message.warning('该用例已在套件中');
      return;
    }
    setSuiteTestcaseIds((prev) => [...prev, addTestcaseId]);
    setAddTestcaseId(undefined);
  }

  async function submitSuite() {
    const values = await form.validateFields();
    if (suiteTestcaseIds.length === 0) {
      message.warning('请至少添加一个用例');
      return;
    }

    const testcaseIds = suiteTestcaseIds.filter((id) => Number.isFinite(id));
    const data: any = {
      name: values.name,
      description: values.description,
      enabled: values.enabled,
      testcase_ids: testcaseIds,
      testcases: testcaseIds.map((id, idx) => ({
        testcase_id: id,
        order: idx + 1,
        enabled: true,
      })),
    };

    if (editingSuite) {
      updateMutation.mutate({ id: editingSuite.id, data });
    } else {
      createMutation.mutate(data);
    }
  }

  async function handleBatchDelete() {
    if (!selectedRowKeys.length) {
      message.warning('请先选择要删除的套件');
      return;
    }
    try {
      await Promise.all(selectedRowKeys.map((id) => deleteSuite(Number(id))));
      message.success(`已删除 ${selectedRowKeys.length} 个套件`);
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['suites'] });
    } catch (e: any) {
      message.error(e?.response?.data?.message || '批量删除失败');
    }
  }

  function openSingleRunModal(suite: Suite) {
    setSelectedSuite(suite);
    setDeviceSerial('');
    setRunModalOpen(true);
  }

  function confirmSingleRun() {
    if (!selectedSuite) return;
    if (!deviceSerial) {
      message.warning('请选择设备');
      return;
    }
    executeMutation.mutate({ suiteIds: [selectedSuite.id], serial: deviceSerial });
  }

  function confirmBatchRun() {
    if (!selectedRowKeys.length) {
      message.warning('请先选择要执行的套件');
      return;
    }
    if (!deviceSerial) {
      message.warning('请选择设备');
      return;
    }
    executeMutation.mutate({
      suiteIds: selectedRowKeys.map((x) => Number(x)),
      serial: deviceSerial,
    });
  }

  const availableTestcaseOptions = useMemo(
    () =>
      testcases
        .filter((tc: any) => !suiteTestcaseIds.includes(tc.id))
        .map((tc: any) => ({
          label: `${tc.name} (${tc.priority})`,
          value: tc.id,
        })),
    [testcases, suiteTestcaseIds],
  );

  const columns: ColumnsType<Suite> = [
    {
      title: '名称',
      dataIndex: 'name',
      width: 240,
      render: (v: string) => <strong>{v}</strong>,
    },
    {
      title: '用例数',
      dataIndex: 'testcase_count',
      width: 100,
      render: (v: number) => `${v} 个`,
    },
    {
      title: '总步骤',
      dataIndex: 'total_step_count',
      width: 100,
      render: (v: number) => `${v} 步`,
    },
    {
      title: '预计时长',
      dataIndex: 'estimated_duration',
      width: 120,
      render: (v: number) => (v ? `${Math.floor(v / 60)}分${v % 60}秒` : '-'),
    },
    {
      title: '启用',
      dataIndex: 'enabled',
      width: 90,
      render: (v: boolean, row: Suite) => (
        <Switch
          checked={v}
          size="small"
          onChange={(checked) => toggleEnabledMutation.mutate({ id: row.id, enabled: checked })}
        />
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (v?: string) => v || <span style={{ color: '#bfbfbf' }}>-</span>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: '操作',
      width: 220,
      fixed: 'right',
      render: (_: any, row: Suite) => (
        <Space size="small">
          <Tooltip title="执行">
            <Button size="small" icon={<PlayCircleOutlined />} onClick={() => openSingleRunModal(row)} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(row)} />
          </Tooltip>
          <Tooltip title="复制">
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => duplicateMutation.mutate({ id: row.id, name: `${row.name}-副本` })}
            />
          </Tooltip>
          <Popconfirm title={`确认删除套件「${row.name}」？`} onConfirm={() => deleteMutation.mutate(row.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={`套件管理（共 ${total} 条）`}
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ['suites'] })}>
              刷新
            </Button>
            {selectedRowKeys.length > 0 ? (
              <>
                <Button icon={<ThunderboltOutlined />} onClick={() => setBatchRunModalOpen(true)}>
                  批量执行 ({selectedRowKeys.length})
                </Button>
                <Button danger icon={<DeleteOutlined />} onClick={handleBatchDelete}>
                  批量删除
                </Button>
              </>
            ) : null}
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
              新建套件
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Search
            allowClear
            placeholder="搜索套件名称"
            style={{ width: 260 }}
            onSearch={setSearchText}
            onChange={(e) => {
              if (!e.target.value) {
                setSearchText('');
              }
            }}
          />
        </Space>

        <Table<Suite>
          rowKey="id"
          loading={suitesLoading}
          dataSource={suites}
          columns={columns}
          scroll={{ x: 1200 }}
          rowSelection={{ selectedRowKeys, onChange: setSelectedRowKeys }}
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
        title={editingSuite ? `编辑套件: ${editingSuite.name}` : '新建套件'}
        open={modalOpen}
        width={860}
        onCancel={closeEditModal}
        onOk={submitSuite}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="套件名称" rules={[{ required: true, message: '请输入套件名称' }]}>
            <Input placeholder="例如: 回归测试套件" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item name="enabled" label="状态" valuePropName="checked" initialValue>
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item label="添加用例">
            <Space.Compact style={{ width: '100%' }}>
              <Select
                showSearch
                allowClear
                style={{ width: '100%' }}
                placeholder={testcasesLoading ? '加载用例中...' : '选择要加入的用例'}
                value={addTestcaseId}
                onChange={setAddTestcaseId}
                options={availableTestcaseOptions}
                optionFilterProp="label"
              />
              <Button type="primary" onClick={addTestcase}>
                添加
              </Button>
            </Space.Compact>
          </Form.Item>

          <div style={{ border: '1px solid #f0f0f0', borderRadius: 6, minHeight: 180, padding: 12 }}>
            {suiteTestcaseIds.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前套件还没有用例" />
            ) : (
              <List
                dataSource={suiteTestcaseIds}
                renderItem={(testcaseId, index) => {
                  const testcase = testcaseMap.get(testcaseId);
                  return (
                    <List.Item
                      actions={[
                        <Button
                          key="up"
                          size="small"
                          icon={<ArrowUpOutlined />}
                          onClick={() => moveTestcase(index, -1)}
                          disabled={index === 0}
                        />,
                        <Button
                          key="down"
                          size="small"
                          icon={<ArrowDownOutlined />}
                          onClick={() => moveTestcase(index, 1)}
                          disabled={index === suiteTestcaseIds.length - 1}
                        />,
                        <Button key="remove" size="small" danger onClick={() => removeTestcase(index)}>
                          移除
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Space>
                            <Tag color="blue">#{index + 1}</Tag>
                            <strong>{testcase?.name || `用例ID ${testcaseId}`}</strong>
                            {testcase?.priority ? <Tag>{testcase.priority}</Tag> : null}
                          </Space>
                        }
                        description={
                          testcase ? (
                            <span style={{ color: '#8c8c8c' }}>
                              步骤 {testcase.step_count || 0}，超时 {testcase.timeout || 0}s
                            </span>
                          ) : (
                            <span style={{ color: '#ff4d4f' }}>该用例详情未加载</span>
                          )
                        }
                      />
                    </List.Item>
                  );
                }}
              />
            )}
          </div>
        </Form>
      </Modal>

      <Modal
        title={`执行套件: ${selectedSuite?.name || ''}`}
        open={runModalOpen}
        onCancel={() => {
          setRunModalOpen(false);
          setSelectedSuite(null);
          setDeviceSerial('');
        }}
        onOk={confirmSingleRun}
        confirmLoading={executeMutation.isPending}
      >
        <Select
          style={{ width: '100%' }}
          placeholder="选择设备"
          value={deviceSerial || undefined}
          onChange={setDeviceSerial}
          options={deviceOptions}
        />
      </Modal>

      <Modal
        title={`批量执行套件 (${selectedRowKeys.length})`}
        open={batchRunModalOpen}
        onCancel={() => {
          setBatchRunModalOpen(false);
          setDeviceSerial('');
        }}
        onOk={confirmBatchRun}
        confirmLoading={executeMutation.isPending}
      >
        <Select
          style={{ width: '100%' }}
          placeholder="选择设备"
          value={deviceSerial || undefined}
          onChange={setDeviceSerial}
          options={deviceOptions}
        />
      </Modal>
    </div>
  );
};

export default SuitesPage;
