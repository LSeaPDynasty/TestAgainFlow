import React, { useMemo, useState } from 'react';
import {
  Button,
  Card,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Tooltip,
  message,
  Divider,
  Radio,
  InputNumber,
  List,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  SettingOutlined,
  ExperimentOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getTestPlans,
  getTestPlan,
  createTestPlan,
  updateTestPlan,
  deleteTestPlan,
  toggleTestPlan,
  addSuitesToPlan,
  removeSuitesFromPlan,
  reorderPlanSuites,
  setSuiteTestcaseOrder,
  executeTestPlan,
  type TestPlan,
  type TestPlanDetail,
  type TestPlanCreate,
  type TestPlanSuite,
  type TestPlanTestcaseOrder,
} from '../../services/testPlan';
import { getSuites, type Suite } from '../../services/suite';
import { getTestcases, type Testcase } from '../../services/testcase';
import { getDevices } from '../../services/device';
import { useProject } from '../../contexts/ProjectContext';

const { Search, TextArea } = Input;
const { Option } = Select;

type FormData = {
  name: string;
  description?: string;
  execution_strategy: 'sequential' | 'parallel';
  max_parallel_tasks: number;
  enabled: boolean;
};

const TestPlansPage: React.FC = () => {
  const { selectedProjectId } = useProject();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<FormData>();
  const [runForm] = Form.useForm();

  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [modalOpen, setModalOpen] = useState(false);
  const [configDrawerOpen, setConfigDrawerOpen] = useState(false);
  const [testcaseOrderDrawerOpen, setTestcaseOrderDrawerOpen] = useState(false);
  const [runModalOpen, setRunModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<TestPlan | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<TestPlanDetail | null>(null);
  const [planSuites, setPlanSuites] = useState<TestPlanSuite[]>([]);
  const [selectedSuiteForTestcaseOrder, setSelectedSuiteForTestcaseOrder] = useState<number | null>(null);
  const [orderedTestcases, setOrderedTestcases] = useState<TestPlanTestcaseOrder[]>([]);

  const { data: plansResp, isLoading: plansLoading } = useQuery({
    queryKey: ['testPlans', page, pageSize, searchText, selectedProjectId],
    queryFn: () =>
      getTestPlans({
        page,
        page_size: pageSize,
        project_id: selectedProjectId || undefined,
      }),
  });

  const { data: suitesResp, isLoading: suitesLoading, error: suitesError } = useQuery({
    queryKey: ['suites-for-testplans', selectedProjectId, configDrawerOpen],
    queryFn: async () => {
      // 当没有选择项目时，不传project_id参数，获取所有套件
      const params: any = {
        page: 1,
        page_size: 1000,
      };
      // 只有当明确选择了项目时才传递project_id
      if (selectedProjectId !== undefined && selectedProjectId !== null) {
        params.project_id = selectedProjectId;
      }
      return getSuites(params);
    },
    enabled: configDrawerOpen,
    retry: 1,
  });

  const { data: testcasesResp } = useQuery({
    queryKey: ['testcases-for-testplans', selectedProjectId],
    queryFn: async () => {
      const params: any = {
        page: 1,
        page_size: 1000,
      };
      if (selectedProjectId !== undefined && selectedProjectId !== null) {
        params.project_id = selectedProjectId;
      }
      return getTestcases(params);
    },
    enabled: testcaseOrderDrawerOpen,
  });

  const { data: devicesResp } = useQuery({
    queryKey: ['devices-for-testplans-run'],
    queryFn: () => getDevices({ page: 1, page_size: 200 }),
    enabled: runModalOpen,
  });

  const plans: TestPlan[] = plansResp?.data?.data?.items || [];
  const total = plansResp?.data?.data?.total || 0;
  const suites: Suite[] = suitesResp?.data?.data?.items || [];
  const testcases: Testcase[] = testcasesResp?.data?.data?.items || [];
  const devices = devicesResp?.data?.data?.items || [];

  const deviceOptions = devices.map((d: any) => ({
    label: `${d.name || d.serial} (${d.status})`,
    value: d.serial,
    disabled: d.status !== 'online',
  }));

  const createMutation = useMutation({
    mutationFn: createTestPlan,
    onSuccess: () => {
      message.success('创建成功');
      closeEditModal();
      queryClient.invalidateQueries({ queryKey: ['testPlans'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<TestPlanCreate> }) =>
      updateTestPlan(id, data),
    onSuccess: () => {
      message.success('更新成功');
      closeEditModal();
      queryClient.invalidateQueries({ queryKey: ['testPlans'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTestPlan,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['testPlans'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '删除失败'),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      toggleTestPlan(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testPlans'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '操作失败'),
  });

  const executeMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      executeTestPlan(id, data),
    onSuccess: (resp: any) => {
      message.success(`执行成功，已创建 ${resp?.data?.data?.length || 0} 个运行任务`);
      closeRunModal();
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '执行失败'),
  });

  const addSuitesMutation = useMutation({
    mutationFn: ({ id, suiteIds }: { id: number; suiteIds: number[] }) =>
      addSuitesToPlan(id, suiteIds),
    onSuccess: () => {
      message.success('添加成功');
      queryClient.invalidateQueries({ queryKey: ['testPlans'] });
      loadPlanDetail(selectedPlan?.id || 0);
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '添加失败'),
  });

  const removeSuitesMutation = useMutation({
    mutationFn: ({ id, suiteIds }: { id: number; suiteIds: number[] }) =>
      removeSuitesFromPlan(id, suiteIds),
    onSuccess: () => {
      message.success('移除成功');
      queryClient.invalidateQueries({ queryKey: ['testPlans'] });
      loadPlanDetail(selectedPlan?.id || 0);
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '移除失败'),
  });

  const reorderSuitesMutation = useMutation({
    mutationFn: ({ id, suites }: { id: number; suites: TestPlanSuite[] }) =>
      reorderPlanSuites(id, suites),
    onSuccess: () => {
      message.success('排序更新成功');
      queryClient.invalidateQueries({ queryKey: ['testPlans'] });
      loadPlanDetail(selectedPlan?.id || 0);
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '更新失败'),
  });

  const setTestcaseOrderMutation = useMutation({
    mutationFn: ({
      planId,
      suiteId,
      orders
    }: {
      planId: number;
      suiteId: number;
      orders: TestPlanTestcaseOrder[];
    }) => setSuiteTestcaseOrder(planId, suiteId, orders),
    onSuccess: () => {
      message.success('用例顺序更新成功');
      closeTestcaseOrderDrawer();
      loadPlanDetail(selectedPlan?.id || 0);
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '更新失败'),
  });

  const loadPlanDetail = async (planId: number) => {
    try {
      const resp = await getTestPlan(planId);
      setSelectedPlan(resp.data.data);
      setPlanSuites(resp.data.data.suites || []);
    } catch (e) {
      message.error('加载详情失败');
    }
  };

  const closeEditModal = () => {
    setModalOpen(false);
    setEditingPlan(null);
    form.resetFields();
  };

  const closeConfigDrawer = () => {
    setConfigDrawerOpen(false);
    setSelectedPlan(null);
    setPlanSuites([]);
  };

  const closeTestcaseOrderDrawer = () => {
    setTestcaseOrderDrawerOpen(false);
    setSelectedSuiteForTestcaseOrder(null);
    setOrderedTestcases([]);
  };

  const handleMoveTestcase = (index: number, direction: 'up' | 'down') => {
    const newTestcases = [...orderedTestcases];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newTestcases.length) return;

    [newTestcases[index], newTestcases[targetIndex]] = [newTestcases[targetIndex], newTestcases[index]];

    // Update order_index
    newTestcases.forEach((tc, idx) => {
      tc.order_index = idx + 1;
    });

    setOrderedTestcases(newTestcases);
  };

  const handleSaveTestcaseOrder = () => {
    if (!selectedPlan || !selectedSuiteForTestcaseOrder) return;

    const testcaseOrders = orderedTestcases.map(tc => ({
      testcase_id: tc.testcase_id,
      testcase_name: tc.testcase_name,
      order_index: tc.order_index,
    }));

    setTestcaseOrderMutation.mutate({
      planId: selectedPlan.id,
      suiteId: selectedSuiteForTestcaseOrder,
      orders: testcaseOrders,
    });
  };

  const closeRunModal = () => {
    setRunModalOpen(false);
    // Don't resetFields here because Modal has destroyOnClose
    // The form will be automatically destroyed and recreated
  };

  const openCreateModal = () => {
    setEditingPlan(null);
    form.setFieldsValue({
      name: '',
      description: '',
      execution_strategy: 'sequential',
      max_parallel_tasks: 1,
      enabled: true,
    });
    setModalOpen(true);
  };

  const openEditModal = (plan: TestPlan) => {
    setEditingPlan(plan);
    form.setFieldsValue({
      name: plan.name,
      description: plan.description,
      execution_strategy: plan.execution_strategy,
      max_parallel_tasks: plan.max_parallel_tasks,
      enabled: plan.enabled,
    });
    setModalOpen(true);
  };

  const openConfigDrawer = async (plan: TestPlan) => {
    setSelectedPlan(null);
    setPlanSuites([]);
    setSelectedPlan(plan as any);
    await loadPlanDetail(plan.id);
    setConfigDrawerOpen(true);
  };

  const openTestcaseOrderDrawer = (suiteId: number) => {
    setSelectedSuiteForTestcaseOrder(suiteId);

    // Find the suite and get its testcases
    const suite = planSuites.find(s => s.suite_id === suiteId);
    if (suite && suite.testcases) {
      setOrderedTestcases([...suite.testcases]);
    } else {
      // If no custom order, get default testcases from the suite
      const suiteData = suites.find(s => s.id === suiteId);
      if (suiteData) {
        // Get testcases for this suite from suite detail
        // For now, use empty array - we need to fetch suite detail
        setOrderedTestcases([]);
      }
    }

    setTestcaseOrderDrawerOpen(true);
  };

  const openRunModal = (plan: TestPlan) => {
    setSelectedPlan(plan as any);
    setRunModalOpen(true);
  };

  const handleCreateOrUpdate = async () => {
    try {
      const values = await form.validateFields();
      const data: TestPlanCreate = {
        name: values.name,
        description: values.description,
        execution_strategy: values.execution_strategy,
        max_parallel_tasks: values.max_parallel_tasks,
        enabled: values.enabled,
        project_id: selectedProjectId || undefined,
      };

      if (editingPlan) {
        updateMutation.mutate({ id: editingPlan.id, data });
      } else {
        createMutation.mutate(data);
      }
    } catch (e) {
      // Validation failed
    }
  };

  const handleAddSuites = (suiteIds: number[]) => {
    if (selectedPlan && suiteIds.length > 0) {
      addSuitesMutation.mutate({ id: selectedPlan.id, suiteIds });
    }
  };

  const handleRemoveSuite = (suiteId: number) => {
    if (selectedPlan) {
      removeSuitesMutation.mutate({ id: selectedPlan.id, suiteIds: [suiteId] });
    }
  };

  const handleMoveSuite = (index: number, direction: 'up' | 'down') => {
    const newSuites = [...planSuites];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newSuites.length) return;

    [newSuites[index], newSuites[targetIndex]] = [newSuites[targetIndex], newSuites[index]];

    // Update order_index
    newSuites.forEach((suite, idx) => {
      suite.order_index = idx + 1;
    });

    setPlanSuites(newSuites);

    if (selectedPlan) {
      const reorderData = newSuites.map(s => ({
        suite_id: s.suite_id,
        order: s.order_index,
        enabled: s.enabled,
      }));
      reorderSuitesMutation.mutate({ id: selectedPlan.id, suites: reorderData });
    }
  };

  const handleExecute = async () => {
    try {
      const values = await runForm.validateFields();
      if (!selectedPlan) return;

      executeMutation.mutate({
        id: selectedPlan.id,
        data: {
          platform: values.platform,
          device_serial: values.device_serial,
          profile_id: values.profile_id,
          timeout: values.timeout,
          priority: values.priority,
        },
      });
    } catch (e) {
      // Validation failed
    }
  };

  const columns: ColumnsType<TestPlan> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <Space>
          <span>{text}</span>
          {!record.enabled && <Tag color="red">禁用</Tag>}
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 250,
      ellipsis: true,
    },
    {
      title: '执行策略',
      dataIndex: 'execution_strategy',
      key: 'execution_strategy',
      width: 120,
      render: (text) => (
        <Tag color={text === 'parallel' ? 'blue' : 'green'}>
          {text === 'parallel' ? '并行' : '串行'}
        </Tag>
      ),
    },
    {
      title: '套件数',
      dataIndex: 'suite_count',
      key: 'suite_count',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled, record) => (
        <Switch
          checked={enabled}
          onChange={(checked) =>
            toggleMutation.mutate({ id: record.id, enabled: checked })
          }
          loading={toggleMutation.isPending}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="配置">
            <Button
              type="link"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => openConfigDrawer(record)}
            />
          </Tooltip>
          <Tooltip title="执行">
            <Button
              type="link"
              size="small"
              icon={<PlayCircleOutlined />}
              disabled={!record.enabled}
              onClick={() => openRunModal(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openEditModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除此测试计划？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const availableSuites = useMemo(() => {
    return suites.filter(
      (suite) => !planSuites.find((ps) => ps.suite_id === suite.id)
    );
  }, [suites, planSuites]);

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <ExperimentOutlined />
            <span>测试计划</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => queryClient.invalidateQueries({ queryKey: ['testPlans'] })}
              loading={plansLoading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateModal}
            >
              新建测试计划
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={plans}
          rowKey="id"
          loading={plansLoading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps || 20);
            },
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingPlan ? '编辑测试计划' : '新建测试计划'}
        open={modalOpen}
        onOk={handleCreateOrUpdate}
        onCancel={closeEditModal}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          preserve={false}
        >
          <Form.Item
            label="名称"
            name="name"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入测试计划名称" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>

          <Form.Item
            label="执行策略"
            name="execution_strategy"
            rules={[{ required: true }]}
          >
            <Radio.Group>
              <Radio value="sequential">串行执行</Radio>
              <Radio value="parallel">并行执行</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            label="最大并行数"
            name="max_parallel_tasks"
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="启用状态"
            name="enabled"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Configuration Drawer */}
      <Drawer
        title="配置测试计划"
        open={configDrawerOpen}
        onClose={closeConfigDrawer}
        width={700}
        destroyOnClose
      >
        {selectedPlan && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <h3>{selectedPlan.name}</h3>
              <p>{selectedPlan.description}</p>
            </div>

            <Divider />

            <div style={{ marginBottom: 16 }}>
              <h4>
                添加套件
                <span style={{ fontWeight: 'normal', fontSize: 12, marginLeft: 8, color: '#666' }}>
                  (可用: {availableSuites.length} / 总计: {suites.length})
                </span>
              </h4>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="选择要添加的套件"
                value={[]}
                onChange={(value) => handleAddSuites(value)}
                loading={suitesLoading}
                options={availableSuites.map((s) => ({
                  label: s.name,
                  value: s.id,
                }))}
                notFoundContent={
                  suitesLoading ? '加载中...' :
                  availableSuites.length === 0 && suites.length > 0 ? '所有套件都已添加' :
                  '暂无可用的套件'
                }
              />
              {suitesError && (
                <div style={{ color: '#ff4d4f', marginTop: 8, fontSize: 12 }}>
                  加载失败: {(suitesError as any)?.message || '未知错误'}
                </div>
              )}
              {!suitesLoading && availableSuites.length === 0 && suites.length > 0 && (
                <div style={{ color: '#52c41a', marginTop: 8, fontSize: 12 }}>
                  ✓ 已添加所有 {suites.length} 个套件
                </div>
              )}
              {!suitesLoading && suites.length === 0 && !suitesError && (
                <div style={{ color: '#999', marginTop: 8, fontSize: 12 }}>
                  当前项目下没有可用的套件，请先创建套件
                  {selectedProjectId === undefined && (
                    <span style={{ display: 'block', marginTop: 4, fontSize: 11 }}>
                      💡 提示：未选择项目时，可能无法看到所有套件
                    </span>
                  )}
                </div>
              )}
            </div>

            <Divider />

            <div>
              <h4>已选套件 (按执行顺序)</h4>
              {planSuites.length === 0 ? (
                <Empty description="暂无套件" />
              ) : (
                <List
                  dataSource={planSuites}
                  renderItem={(suite, index) => (
                    <List.Item
                      actions={[
                        <Button
                          size="small"
                          icon={<ArrowUpOutlined />}
                          disabled={index === 0}
                          onClick={() => handleMoveSuite(index, 'up')}
                        />,
                        <Button
                          size="small"
                          icon={<ArrowDownOutlined />}
                          disabled={index === planSuites.length - 1}
                          onClick={() => handleMoveSuite(index, 'down')}
                        />,
                        <Button
                          size="small"
                          type="link"
                          onClick={() => openTestcaseOrderDrawer(suite.suite_id)}
                        >
                          配置用例顺序
                        </Button>,
                        <Popconfirm
                          title="确认移除此套件？"
                          onConfirm={() => handleRemoveSuite(suite.suite_id)}
                          okText="确认"
                          cancelText="取消"
                        >
                          <Button size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>,
                      ]}
                    >
                      <List.Item.Meta
                        title={`${suite.order_index}. ${suite.suite_name || `Suite ${suite.suite_id}`}`}
                        description={`用例数: ${suite.testcases?.length || 0}`}
                      />
                    </List.Item>
                  )}
                />
              )}
            </div>
          </div>
        )}
      </Drawer>

      {/* Testcase Order Drawer */}
      <Drawer
        title="配置用例执行顺序"
        open={testcaseOrderDrawerOpen}
        onClose={closeTestcaseOrderDrawer}
        width={600}
        destroyOnClose
        extra={
          <Button
            type="primary"
            onClick={handleSaveTestcaseOrder}
            loading={setTestcaseOrderMutation.isPending}
          >
            保存顺序
          </Button>
        }
      >
        {selectedPlan && selectedSuiteForTestcaseOrder && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <p style={{ color: '#666', marginBottom: 16 }}>
                调整用例执行顺序后，点击"保存顺序"按钮保存修改
              </p>
            </div>

            {orderedTestcases.length === 0 ? (
              <Empty
                description="暂无用例"
                style={{ margin: '40px 0' }}
              />
            ) : (
              <List
                dataSource={orderedTestcases}
                renderItem={(testcase, index) => (
                  <List.Item
                    style={{
                      cursor: 'move',
                      backgroundColor: index % 2 === 0 ? '#fafafa' : 'white',
                    }}
                    actions={[
                      <Button
                        size="small"
                        icon={<ArrowUpOutlined />}
                        disabled={index === 0}
                        onClick={() => handleMoveTestcase(index, 'up')}
                      />,
                      <Button
                        size="small"
                        icon={<ArrowDownOutlined />}
                        disabled={index === orderedTestcases.length - 1}
                        onClick={() => handleMoveTestcase(index, 'down')}
                      />,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={
                        <div style={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          backgroundColor: '#1890ff',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 'bold',
                        }}>
                          {index + 1}
                        </div>
                      }
                      title={testcase.testcase_name || `Testcase ${testcase.testcase_id}`}
                      description={`优先级: ${testcase.priority || 'P1'}`}
                    />
                  </List.Item>
                )}
              />
            )}
          </div>
        )}
      </Drawer>

      {/* Execution Modal */}
      <Modal
        title="执行测试计划"
        open={runModalOpen}
        onOk={handleExecute}
        onCancel={closeRunModal}
        confirmLoading={executeMutation.isPending}
        destroyOnClose
      >
        <Form
          form={runForm}
          layout="vertical"
          preserve={false}
          initialValues={{
            platform: 'android',
            priority: 'normal',
          }}
        >
          <Form.Item
            label="执行平台"
            name="platform"
            rules={[{ required: true, message: '请选择执行平台' }]}
          >
            <Select>
              <Option value="android">Android</Option>
              <Option value="ios">iOS</Option>
              <Option value="web">Web</Option>
            </Select>
          </Form.Item>

          <Form.Item label="设备序列号" name="device_serial">
            <Select
              placeholder="选择设备"
              allowClear
              options={deviceOptions}
            />
          </Form.Item>

          <Form.Item label="优先级" name="priority">
            <Select>
              <Option value="low">低</Option>
              <Option value="normal">中</Option>
              <Option value="high">高</Option>
            </Select>
          </Form.Item>

          <Form.Item label="超时时间(秒)" name="timeout">
            <InputNumber min={1} placeholder="留空使用默认值" style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TestPlansPage;
