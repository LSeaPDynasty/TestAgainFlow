import React, { useMemo, useState } from 'react';
import {
  Button,
  Card,
  Divider,
  Empty,
  Form,
  Input,
  List,
  Alert,
  Drawer,
  Modal,
  Popconfirm,
  Space,
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
  CodeOutlined,
  AppstoreOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getFlows,
  getFlow,
  createFlow,
  updateFlow,
  deleteFlow,
  duplicateFlow,
  validateDsl,
  type Flow,
  type FlowCreate,
} from '../../services/flow';
import { getSteps } from '../../services/step';
import { getActionTypes, type ActionTypeConfig } from '../../services/actionTypes';
import { useProject } from '../../contexts/ProjectContext';
import DrawerSelector from '../../components/DrawerSelector';

const { Search, TextArea } = Input;

const FLOW_TYPES = [
  { value: 'standard', label: '标准流程' },
  { value: 'dsl', label: 'DSL 流程' },
  { value: 'python', label: 'Python 脚本' },
] as const;

type FlowType = (typeof FLOW_TYPES)[number]['value'];
type ComposeStep = {
  step_id?: number;
  sub_flow_id?: number;
  order: number;
  override_value?: string;
};

type FormData = {
  name: string;
  description?: string;
  flow_type: FlowType;
  dsl_content?: string;
};

const FlowsPage: React.FC = () => {
  const { selectedProjectId } = useProject();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<FormData>();

  const [searchText, setSearchText] = useState('');
  const [selectedType, setSelectedType] = useState<FlowType | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingFlow, setEditingFlow] = useState<Flow | null>(null);
  const [composeSteps, setComposeSteps] = useState<ComposeStep[]>([]);
  const [stepPickerOpen, setStepPickerOpen] = useState(false);
  const [subFlowPickerOpen, setSubFlowPickerOpen] = useState(false);

  const [stepKeyword, setStepKeyword] = useState('');
  const [subFlowKeyword, setSubFlowKeyword] = useState('');

  const flowType = Form.useWatch('flow_type', form) || 'standard';
  const isVisual = flowType === 'standard';
  const isDslEditor = flowType === 'dsl' || flowType === 'python';

  const { data: flowsResp, isLoading: flowsLoading } = useQuery({
    queryKey: ['flows', page, pageSize, searchText, selectedType, selectedProjectId],
    queryFn: () =>
      getFlows({
        page,
        page_size: pageSize,
        search: searchText || undefined,
        flow_type: selectedType,
        include_stats: true,
        project_id: selectedProjectId || undefined,
      }),
  });

  const { data: stepsResp, isLoading: stepsLoading } = useQuery({
    queryKey: ['steps-for-flow-editor', selectedProjectId],
    queryFn: () => getSteps({ page: 1, page_size: 1000, project_id: selectedProjectId || undefined }),
    enabled: modalOpen,
  });

  const { data: subFlowsResp, isLoading: subFlowsLoading } = useQuery({
    queryKey: ['sub-flows-for-flow-editor', selectedProjectId, editingFlow?.id],
    queryFn: () => getFlows({ page: 1, page_size: 1000, flow_type: 'standard', project_id: selectedProjectId || undefined }),
    enabled: modalOpen,
  });

  const { data: actionTypesResponse } = useQuery({
    queryKey: ['action-types'],
    queryFn: () => getActionTypes(),
    staleTime: 5 * 60 * 1000,
  });

  const flowItems: Flow[] = flowsResp?.data?.data?.items || [];
  const total = flowsResp?.data?.data?.total || 0;
  const actionTypeItems = actionTypesResponse?.items || [];

  // 根据type_code获取操作类型的详细信息
  const getActionTypeInfo = (typeCode: string): ActionTypeConfig | undefined => {
    return actionTypeItems.find(item => item.type_code === typeCode);
  };
  const stepsList: any[] = stepsResp?.data?.data?.items || [];
  const subFlowsList: any[] = (subFlowsResp?.data?.data?.items || []).filter((x: any) => x.id !== editingFlow?.id);

  const createMutation = useMutation({
    mutationFn: createFlow,
    onSuccess: () => {
      message.success('创建成功');
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      closeModal();
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<FlowCreate> }) => updateFlow(id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['flows'] });
      closeModal();
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFlow,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['flows'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '删除失败'),
  });

  const duplicateMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) => duplicateFlow(id, { new_name: name }),
    onSuccess: () => {
      message.success('复制成功');
      queryClient.invalidateQueries({ queryKey: ['flows'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '复制失败'),
  });

  const validateDslMutation = useMutation({
    mutationFn: validateDsl,
    onSuccess: (resp: any) => {
      const valid = resp?.data?.valid;
      if (valid) {
        message.success(`DSL 校验通过，共 ${resp?.data?.expanded_count || 0} 个展开步骤`);
      } else {
        message.error(`DSL 校验失败：${(resp?.data?.errors || []).join('，')}`);
      }
    },
    onError: () => message.error('DSL 校验失败'),
  });

  function resetComposeOrder(list: ComposeStep[]) {
    return list.map((item, idx) => ({ ...item, order: idx + 1 }));
  }

  function closeModal() {
    setModalOpen(false);
    setEditingFlow(null);
    setComposeSteps([]);
    setStepPickerOpen(false);
    setSubFlowPickerOpen(false);
    setStepKeyword('');
    setSubFlowKeyword('');
    form.resetFields();
  }

  async function openCreate() {
    setEditingFlow(null);
    setComposeSteps([]);
    form.setFieldsValue({
      name: '',
      description: '',
      flow_type: 'standard',
      dsl_content: '',
    });
    setModalOpen(true);
  }

  async function openEdit(flow: Flow) {
    setEditingFlow(flow);
    form.setFieldsValue({
      name: flow.name,
      description: flow.description || '',
      flow_type: flow.flow_type,
      dsl_content: flow.dsl_content || '',
    });
    setComposeSteps([]);
    setModalOpen(true);

    if (flow.flow_type !== 'standard') {
      return;
    }

    try {
      const detailResp = await getFlow(flow.id);
      const rawSteps = detailResp?.data?.data?.steps || [];
      const mapped: ComposeStep[] = rawSteps.map((item: any, idx: number) => ({
        step_id: item.step_id,
        sub_flow_id: item.sub_flow_id,
        order: item.order || idx + 1,
        override_value: item.override_value,
      }));
      setComposeSteps(resetComposeOrder(mapped));
    } catch {
      setComposeSteps([]);
      message.warning('流程详情加载失败，已使用空步骤列表');
    }
  }

  async function handleSubmit() {
    const values = await form.validateFields();
    const payload: Partial<FlowCreate> = {
      name: values.name,
      description: values.description,
      flow_type: values.flow_type,
    };

    if (values.flow_type === 'standard') {
      if (composeSteps.length === 0) {
        message.warning('标准流程至少需要 1 个步骤或子流程');
        return;
      }
      payload.steps = resetComposeOrder(composeSteps) as any;
      payload.dsl_content = undefined;
    } else {
      payload.dsl_content = values.dsl_content || '';
      payload.steps = undefined;
    }

    if (editingFlow) {
      updateMutation.mutate({ id: editingFlow.id, data: payload });
    } else {
      createMutation.mutate(payload as FlowCreate);
    }
  }

  function addStep(step: any) {
    setComposeSteps((prev) =>
      resetComposeOrder([
        ...prev,
        {
          step_id: step.id,
          order: prev.length + 1,
          override_value: undefined,
        },
      ]),
    );
    setStepPickerOpen(false);
    message.success(`已添加步骤: ${step.name}`);
  }

  function addSubFlow(flow: any) {
    setComposeSteps((prev) =>
      resetComposeOrder([
        ...prev,
        {
          sub_flow_id: flow.id,
          order: prev.length + 1,
          override_value: undefined,
        },
      ]),
    );
    setSubFlowPickerOpen(false);
    message.success(`已添加子流程: ${flow.name}`);
  }

  function moveCompose(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= composeSteps.length) {
      return;
    }
    const next = [...composeSteps];
    [next[index], next[target]] = [next[target], next[index]];
    setComposeSteps(resetComposeOrder(next));
  }

  function removeCompose(index: number) {
    setComposeSteps((prev) => resetComposeOrder(prev.filter((_, i) => i !== index)));
  }

  async function handleValidateDsl() {
    const values = await form.validateFields(['dsl_content']);
    validateDslMutation.mutate({ dsl_content: values.dsl_content || '' });
  }

  const filteredStepCandidates = useMemo(() => {
    if (!stepKeyword.trim()) {
      return stepsList;
    }
    const keyword = stepKeyword.toLowerCase();
    return stepsList.filter(
      (s: any) =>
        String(s?.name || '').toLowerCase().includes(keyword) ||
        String(s?.action_type || '').toLowerCase().includes(keyword) ||
        String(s?.screen_name || '').toLowerCase().includes(keyword),
    );
  }, [stepsList, stepKeyword]);

  const filteredSubFlowCandidates = useMemo(() => {
    if (!subFlowKeyword.trim()) {
      return subFlowsList;
    }
    const keyword = subFlowKeyword.toLowerCase();
    return subFlowsList.filter(
      (f: any) =>
        String(f?.name || '').toLowerCase().includes(keyword) ||
        String(f?.description || '').toLowerCase().includes(keyword),
    );
  }, [subFlowsList, subFlowKeyword]);

  const columns: ColumnsType<Flow> = [
    {
      title: '名称',
      dataIndex: 'name',
      width: 260,
      render: (v: string) => <strong>{v}</strong>,
    },
    {
      title: '类型',
      dataIndex: 'flow_type',
      width: 120,
      render: (v: string) => {
        const config = FLOW_TYPES.find((x) => x.value === v);
        const color = v === 'standard' ? 'green' : v === 'dsl' ? 'purple' : 'blue';
        return <Tag color={color}>{config?.label || v}</Tag>;
      },
    },
    {
      title: '步骤数',
      width: 130,
      render: (_: any, row: Flow) => <span>{row.step_count} / {row.expanded_step_count || 0}</span>,
    },
    {
      title: '被引用',
      dataIndex: 'referenced_by_testcase_count',
      width: 110,
      render: (v: number) => <Tag color={v > 0 ? 'blue' : 'default'}>{v} 个用例</Tag>,
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
      width: 180,
      fixed: 'right',
      render: (_: any, row: Flow) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(row)} />
          </Tooltip>
          <Tooltip title="复制">
            <Button size="small" icon={<CopyOutlined />} onClick={() => duplicateMutation.mutate({ id: row.id, name: `${row.name}-副本` })} />
          </Tooltip>
          <Popconfirm title={`确认删除流程「${row.name}」？`} onConfirm={() => deleteMutation.mutate(row.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={`流程管理（共 ${total} 条）`}
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ['flows'] })}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              新建流程
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Search
            allowClear
            placeholder="搜索流程名称"
            style={{ width: 260 }}
            onSearch={setSearchText}
            onChange={(e) => {
              if (!e.target.value) {
                setSearchText('');
              }
            }}
          />
          <DrawerSelector
            placeholder="流程类型"
            options={FLOW_TYPES.map((x) => ({
              value: x.value,
              label: x.label,
            }))}
            value={selectedType}
            onChange={(v) => setSelectedType(v)}
            drawerWidth={360}
            placement="right"
          />
        </Space>

        <Table<Flow>
          rowKey="id"
          loading={flowsLoading}
          dataSource={flowItems}
          columns={columns}
          scroll={{ x: 1100 }}
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

      <Drawer
        title={editingFlow ? `编辑流程: ${editingFlow.name}` : '新建流程'}
        open={modalOpen}
        onClose={closeModal}
        width="66vw"
        destroyOnClose
        extra={
          <Space>
            <Button onClick={closeModal}>取消</Button>
            <Button type="primary" loading={createMutation.isPending || updateMutation.isPending} onClick={handleSubmit}>
              保存
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 12 }}
            message="标准流程适合可视化编排；DSL/Python 适合复杂逻辑。"
          />
          <Form.Item name="name" label="流程名称" rules={[{ required: true, message: '请输入流程名称' }]}>
            <Input placeholder="例如: 登录并进入首页" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item name="flow_type" label="流程类型" rules={[{ required: true, message: '请选择流程类型' }]}>
            <DrawerSelector
              placeholder="请选择流程类型"
              options={FLOW_TYPES.map((x) => ({
                value: x.value,
                label: x.label,
              }))}
              drawerWidth={360}
              placement="right"
            />
          </Form.Item>

          {isVisual ? (
            <>
              <Divider orientation="left">步骤编排</Divider>
              <Space style={{ marginBottom: 12 }}>
                <Button icon={<AppstoreOutlined />} onClick={() => setStepPickerOpen(true)}>
                  添加步骤
                </Button>
                <Button icon={<PlayCircleOutlined />} onClick={() => setSubFlowPickerOpen(true)}>
                  添加子流程
                </Button>
              </Space>

              <div style={{ border: '1px solid #f0f0f0', borderRadius: 6, padding: 12, minHeight: 180 }}>
                {composeSteps.length === 0 ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无步骤，点击上方按钮添加" />
                ) : (
                  <List
                    dataSource={composeSteps}
                    renderItem={(item, index) => {
                      const isSubFlow = Boolean(item.sub_flow_id);
                      const step = !isSubFlow ? stepsList.find((x: any) => x.id === item.step_id) : null;
                      const subFlow = isSubFlow ? subFlowsList.find((x: any) => x.id === item.sub_flow_id) : null;
                      return (
                        <List.Item
                          actions={[
                            <Button
                              key="up"
                              size="small"
                              icon={<ArrowUpOutlined />}
                              onClick={() => moveCompose(index, -1)}
                              disabled={index === 0}
                            />,
                            <Button
                              key="down"
                              size="small"
                              icon={<ArrowDownOutlined />}
                              onClick={() => moveCompose(index, 1)}
                              disabled={index === composeSteps.length - 1}
                            />,
                            <Button key="delete" size="small" danger onClick={() => removeCompose(index)}>
                              移除
                            </Button>,
                          ]}
                        >
                          <List.Item.Meta
                            title={
                              <Space>
                                <Tag color={isSubFlow ? 'green' : 'blue'}>{isSubFlow ? '子流程' : '步骤'}</Tag>
                                <strong>{isSubFlow ? subFlow?.name || `子流程#${item.sub_flow_id}` : step?.name || `步骤#${item.step_id}`}</strong>
                              </Space>
                            }
                            description={
                              isSubFlow ? (
                                <span>{subFlow?.description || `共 ${subFlow?.step_count || 0} 个步骤`}</span>
                              ) : (
                                <Space>
                                  <Tag>{(() => {
                                    const actionInfo = getActionTypeInfo(step?.action_type || '');
                                    return actionInfo?.display_name || step?.action_type || '-';
                                  })()}</Tag>
                                  <span>{step?.screen_name || '-'}</span>
                                  {step?.element_name ? <span>{step.element_name}</span> : null}
                                </Space>
                              )
                            }
                          />
                        </List.Item>
                      );
                    }}
                  />
                )}
              </div>
            </>
          ) : (
            <>
              <Form.Item name="dsl_content" label={flowType === 'python' ? 'Python 内容' : 'DSL 内容'}>
                <TextArea
                  rows={16}
                  style={{ fontFamily: 'Consolas, Monaco, monospace' }}
                  placeholder={
                    flowType === 'python'
                      ? '# 在这里填写 Python 脚本内容'
                      : 'steps:\n  - step_id: 1\n    order: 1\n  - step_id: 2\n    order: 2'
                  }
                />
              </Form.Item>
              {flowType === 'dsl' ? (
                <Button onClick={handleValidateDsl} loading={validateDslMutation.isPending} icon={<CodeOutlined />}>
                  校验 DSL
                </Button>
              ) : null}
            </>
          )}
        </Form>
      </Drawer>

      <Modal
        title="选择步骤"
        open={stepPickerOpen}
        onCancel={() => setStepPickerOpen(false)}
        footer={null}
        width={780}
      >
        <Search
          allowClear
          placeholder="按名称 / action_type / screen 搜索"
          onSearch={setStepKeyword}
          onChange={(e) => {
            if (!e.target.value) {
              setStepKeyword('');
            }
          }}
          style={{ marginBottom: 12 }}
        />
        {stepsLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>加载中...</div>
        ) : filteredStepCandidates.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="未找到可选步骤" />
        ) : (
          <List
            dataSource={filteredStepCandidates}
            renderItem={(step: any) => (
              <List.Item
                actions={[
                  <Button key="add" type="primary" size="small" onClick={() => addStep(step)}>
                    添加
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={<strong>{step.name}</strong>}
                  description={
                    <Space>
                      <Tag color="blue">{(() => {
                        const actionInfo = getActionTypeInfo(step.action_type || '');
                        return actionInfo?.display_name || step.action_type || '-';
                      })()}</Tag>
                      <span>{step.screen_name || '-'}</span>
                      {step.element_name ? <span>{step.element_name}</span> : null}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Modal>

      <Modal
        title="选择子流程"
        open={subFlowPickerOpen}
        onCancel={() => setSubFlowPickerOpen(false)}
        footer={null}
        width={780}
      >
        <Search
          allowClear
          placeholder="按流程名称/描述搜索"
          onSearch={setSubFlowKeyword}
          onChange={(e) => {
            if (!e.target.value) {
              setSubFlowKeyword('');
            }
          }}
          style={{ marginBottom: 12 }}
        />
        {subFlowsLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>加载中...</div>
        ) : filteredSubFlowCandidates.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有可选子流程" />
        ) : (
          <List
            dataSource={filteredSubFlowCandidates}
            renderItem={(flow: any) => (
              <List.Item
                actions={[
                  <Button key="add" type="primary" size="small" onClick={() => addSubFlow(flow)}>
                    添加
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={<strong>{flow.name}</strong>}
                  description={
                    <Space>
                      <Tag color="green">标准流程</Tag>
                      <span>{flow.step_count || 0} 步</span>
                      {flow.description ? <span>{flow.description}</span> : null}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Modal>
    </div>
  );
};

export default FlowsPage;
