import React, { useState, useMemo } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Input,
  Tag,
  Drawer,
  Form,
  message,
  Popconfirm,
  Tooltip,
  InputNumber,
  Switch,
  Alert,
  Divider,
  Typography,
  Popover,
} from 'antd';

const { Text } = Typography;
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  CopyOutlined,
  QuestionCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSteps, createStep, updateStep, deleteStep, ACTION_TYPES } from '../../services/step';
import { getScreens } from '../../services/screen';
import { getElements } from '../../services/element';
import { getFlows } from '../../services/flow';
import { getActionTypes, actionTypesToCategories, actionTypesToColors, actionRequiresElement } from '../../services/actionTypes';
import DrawerSelector from '../../components/DrawerSelector';
import { VirtualTable } from '../../components/ui';
import AIDescription from '../../components/AIDescription';

const { Search } = Input;
const { TextArea } = Input;

// 类型定义
type Step = {
  id: number;
  name: string;
  description?: string;
  screen_id: number;
  screen_name?: string;
  element_id?: number;
  element_name?: string;
  action_type: string;
  action_value?: string;
  assertions?: any[];
  wait_time?: number;
  continue_on_error?: boolean;
  created_at: string;
  updated_at: string;
};

type StepCreate = {
  name: string;
  description?: string;
  screen_id: number;
  element_id?: number;
  action_type: string;
  action_value?: string;
  assertions?: any[];
  wait_time?: number;
};

type Screen = {
  id: number;
  name: string;
  description?: string;
  app_id?: number;
  element_count: number;
  created_at: string;
  updated_at: string;
};

type Element = {
  id: number;
  name: string;
  description?: string;
  screen_id: number;
  screen_name?: string;
  locators: Array<{
    type: string;
    value: string;
    priority: number;
  }>;
  created_at: string;
  updated_at: string;
};

// 兼容旧代码的默认值（fallback）
const FALLBACK_ACTION_TYPE_CATEGORIES = {
  '设备操作': ['click', 'long_press', 'input', 'swipe', 'hardware_back'],
  '等待': ['wait_element', 'wait_time'],
  '断言': ['assert_text', 'assert_exists', 'assert_not_exists', 'assert_color'],
  '控制流': ['repeat', 'break_if', 'set', 'call'],
  '系统': ['start_activity', 'screenshot'],
};

const Steps: React.FC = () => {
  // 获取操作类型列表（动态）
  const { data: actionTypesResponse, isLoading: actionTypesLoading } = useQuery({
    queryKey: ['action-types'],
    queryFn: () => getActionTypes(),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });

  // 使用动态数据或fallback
  const actionTypeItems = actionTypesResponse?.items || [];
  const ACTION_TYPE_CATEGORIES = useMemo(() => {
    if (actionTypesResponse?.categories) {
      return actionTypesResponse.categories;
    }
    return FALLBACK_ACTION_TYPE_CATEGORIES;
  }, [actionTypesResponse]);

  const ACTION_TYPE_COLORS = useMemo(() => {
    if (actionTypeItems.length > 0) {
      return actionTypesToColors(actionTypeItems);
    }
    return {
      click: 'blue',
      long_press: 'cyan',
      input: 'green',
      swipe: 'purple',
      hardware_back: 'default',
      wait_element: 'orange',
      wait_time: 'orange',
      assert_text: 'red',
      assert_exists: 'magenta',
      assert_not_exists: 'volcano',
      assert_color: 'red',
      repeat: 'geekblue',
      break_if: 'geekblue',
      set: 'geekblue',
      call: 'lime',
    };
  }, [actionTypeItems]);

  // 根据type_code获取操作类型的详细信息
  const getActionTypeInfo = (typeCode: string) => {
    return actionTypeItems.find(item => item.type_code === typeCode);
  };

  const [searchText, setSearchText] = useState('');
  const [selectedScreen, setSelectedScreen] = useState<number | undefined>();
  const [selectedActionType, setSelectedActionType] = useState<string | undefined>();
  const [currentActionType, setCurrentActionType] = useState<string>('click');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingStep, setEditingStep] = useState<Step | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [useVirtualScroll, setUseVirtualScroll] = useState(false);
  const [form] = Form.useForm();

  const queryClient = useQueryClient();

  // 获取步骤列表
  const { data: stepsData, isLoading } = useQuery({
    queryKey: ['steps', page, pageSize, searchText, selectedScreen, selectedActionType],
    queryFn: () =>
      getSteps({
        page,
        page_size: pageSize,
        search: searchText || undefined,
        screen_id: selectedScreen,
        action_type: selectedActionType,
      }),
  });

  // 获取界面列表
  const { data: screensData, isLoading: screensLoading } = useQuery({
    queryKey: ['screens-steps'],
    queryFn: async () => {
      const response = await getScreens({ page: 1, page_size: 1000 });
      console.log('Steps - Screens API response:', response);
      return response;
    },
  });

  // 获取元素列表（根据选中的界面动态获取）
  const { data: elementsData, isLoading: elementsLoading } = useQuery({
    queryKey: ['elements-step-form', selectedScreen],
    queryFn: async () => {
      if (!selectedScreen) return { data: { data: { data: { items: [] } } } };
      const response = await getElements({ screen_id: selectedScreen, page: 1, page_size: 1000 });
      console.log('Steps - Elements API response:', response);
      return response;
    },
    enabled: !!selectedScreen && currentActionType !== 'call',
  });

  // 获取流程列表（用于call操作）
  const { data: flowsData, isLoading: flowsLoading } = useQuery({
    queryKey: ['flows-step-form'],
    queryFn: async () => {
      const response = await getFlows({ page: 1, page_size: 1000, flow_type: 'standard' });
      return response;
    },
    enabled: isModalVisible,
  });

  const screensList = screensData?.data?.data?.items || [];
  const elementsList = elementsData?.data?.data?.items || [];
  const flowsList = flowsData?.data?.data?.items || [];
  console.log('Steps - screensList:', screensList);
  console.log('Steps - elementsList:', elementsList);
  console.log('Steps - flowsList:', flowsList);

  // 删除旧的重复定义
  // const screensList = screensData?.data?.data?.items || [];
  // const elementsList = elementsData?.data?.data?.items || [];

  // 创建步骤
  const createMutation = useMutation({
    mutationFn: createStep,
    onSuccess: () => {
      message.success('创建成功');
      queryClient.invalidateQueries({ queryKey: ['steps'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // 更新步骤
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateStep(id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['steps'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 删除步骤
  const deleteMutation = useMutation({
    mutationFn: deleteStep,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['steps'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  const totalSteps = stepsData?.data?.data?.total || 0;
  const items = stepsData?.data?.data?.items || [];
  // screensList 和 elementsList 已在前面定义

  const handleModalOpen = (step?: Step) => {
    if (step) {
      setEditingStep(step);
      form.setFieldsValue(step);
      setSelectedScreen(step.screen_id);
      setCurrentActionType(step.action_type || 'click');
    } else {
      setEditingStep(null);
      form.resetFields();
      form.setFieldsValue({ action_type: 'click' });
      setCurrentActionType('click');
    }
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingStep(null);
    form.resetFields();
    setSelectedScreen(undefined);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingStep) {
        updateMutation.mutate({ id: editingStep.id, data: values });
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
      title: '步骤名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <strong>{name}</strong>,
    },
    {
      title: '操作类型',
      dataIndex: 'action_type',
      key: 'action_type',
      render: (actionType: string) => {
        const actionInfo = getActionTypeInfo(actionType);
        const displayName = actionInfo?.display_name || actionType;
        const category = actionInfo?.category || '';
        return (
          <Tag color={ACTION_TYPE_COLORS[actionType] || 'default'}>
            {displayName}
          </Tag>
        );
      },
    },
    {
      title: '所属界面',
      dataIndex: 'screen_name',
      key: 'screen_name',
      render: (name: string) => (name ? <Tag color="blue">{name}</Tag> : '-'),
    },
    {
      title: '目标元素',
      dataIndex: 'element_name',
      key: 'element_name',
      render: (name: string) => name || '-',
    },
    {
      title: '操作值',
      dataIndex: 'action_value',
      key: 'action_value',
      render: (value: string) => {
        if (!value) return '-';
        const maxLength = 30;
        return value.length > maxLength ? (
          <Tooltip title={value}>
            <span>{value.substring(0, maxLength)}...</span>
          </Tooltip>
        ) : (
          <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{value}</span>
        );
      },
    },
    {
      title: '等待时间',
      dataIndex: 'wait_time',
      key: 'wait_time',
      render: (time: number) => (time ? `${time}ms` : '-'),
    },
    {
      title: '失败继续',
      dataIndex: 'continue_on_error',
      key: 'continue_on_error',
      width: 100,
      render: (enabled: boolean, record: Step) => (
        <Tooltip title={enabled ? "此步骤失败后会继续执行后续步骤" : "此步骤失败后会中断流程"}>
          <Tag color={enabled ? 'orange' : 'default'} style={{ cursor: 'help' }}>
            {enabled ? '✓ 继续' : '✗ 停止'}
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: 200,
      render: (description: string) => {
        if (!description) {
          return <span style={{ color: '#bfbfbf' }}>-</span>;
        }
        return (
          <Tooltip title={description}>
            <span
              style={{
                display: 'inline-block',
                maxWidth: 180,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {description}
            </span>
          </Tooltip>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: Step) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleModalOpen(record)}
            />
          </Tooltip>
          <Tooltip title="复制">
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => {
                const copied = { ...record };
                delete (copied as any).id;
                handleModalOpen(copied as any);
              }}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description={`确定要删除步骤 "${record.name}" 吗？此操作不可恢复。`}
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

  // 判断是否需要显示元素选择（使用动态数据）
  const needsElement = (actionType?: string) => {
    if (!actionType) return false;
    // 优先使用动态数据
    if (actionTypeItems.length > 0) {
      return actionRequiresElement(actionType, actionTypeItems);
    }
    // fallback到硬编码列表
    return ['click', 'long_press', 'input', 'swipe', 'wait_element', 'assert_exists', 'assert_not_exists', 'assert_text', 'assert_color'].includes(actionType);
  };

  // 判断是否需要显示操作值输入（使用动态数据）
  const needsActionValue = (actionType?: string) => {
    if (!actionType) return false;
    // 优先使用动态数据
    if (actionTypeItems.length > 0) {
      const action = actionTypeItems.find(item => item.type_code === actionType);
      return action?.requires_value ?? false;
    }
    // fallback到硬编码列表
    return ['input', 'swipe', 'assert_text', 'start_activity', 'set'].includes(actionType);
  };

  // 判断是否是断言类型
  const isAssertionType = (actionType?: string) => {
    if (!actionType) return false;
    return actionType.startsWith('assert_');
  };

  return (
    <div>
      <Card
        title={
          <Space>
            <span>步骤管理</span>
            <span style={{ color: '#8c8c8c', fontSize: '14px' }}>共 {totalSteps} 条</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleModalOpen()}>
            新建步骤
          </Button>
        }
      >
        {/* 筛选栏 */}
        <Space style={{ marginBottom: '16px' }} size="middle" wrap>
          <Search
            placeholder="搜索步骤名称"
            allowClear
            style={{ width: 240 }}
            onSearch={setSearchText}
            enterButton={<SearchOutlined />}
          />
          <DrawerSelector
            placeholder="所属界面"
            options={screensList.map((screen: Screen) => ({
              value: screen.id,
              label: screen.name,
              description: `${screen.element_count} 个元素`,
            }))}
            value={selectedScreen}
            onChange={setSelectedScreen}
            drawerWidth={400}
            placement="right"
          />
          <DrawerSelector
            placeholder="操作类型"
            options={Object.entries(ACTION_TYPE_CATEGORIES).flatMap(([category, types]) =>
              types.map((type) => ({
                value: type,
                label: type,
                description: category,
                extra: <Tag color={ACTION_TYPE_COLORS[type] || 'default'}>{category}</Tag>,
              }))
            )}
            value={selectedActionType}
            onChange={setSelectedActionType}
            drawerWidth={360}
            placement="right"
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['steps'] })}
          >
            刷新
          </Button>
          <Tooltip title={useVirtualScroll ? '切换到普通表格' : '切换到虚拟滚动（适合大数据量）'}>
            <Button
              type={useVirtualScroll ? 'primary' : 'default'}
              icon={<ThunderboltOutlined />}
              onClick={() => setUseVirtualScroll(!useVirtualScroll)}
            >
              {useVirtualScroll ? '虚拟滚动' : '普通表格'}
            </Button>
          </Tooltip>
        </Space>

        {useVirtualScroll ? (
          <VirtualTable
            items={items}
            height={600}
            itemHeight={55}
            columns={[
              { key: 'index', title: '序号', width: 80 },
              { key: 'name', title: '步骤名称', width: 150 },
              { key: 'action_type', title: '操作类型', width: 120 },
              { key: 'screen_name', title: '所属界面', width: 120 },
              { key: 'element_name', title: '目标元素', width: 150 },
              { key: 'action_value', title: '操作值', width: 150 },
              { key: 'wait_time', title: '等待时间', width: 100 },
              { key: 'continue_on_error', title: '失败继续', width: 100 },
              { key: 'description', title: '描述', width: 200 },
              { key: 'created_at', title: '创建时间', width: 160 },
              { key: 'actions', title: '操作', width: 180 },
            ]}
            renderItem={(item: Step, index: number) => (
              <tr className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 border-b">
                  <span style={{ color: '#8c8c8c', fontFamily: 'monospace' }}>
                    {(index + 1).toString().padStart(2, '0')}
                  </span>
                </td>
                <td className="px-4 py-3 border-b font-medium">{item.name}</td>
                <td className="px-4 py-3 border-b">
                  <Tag color={ACTION_TYPE_COLORS[item.action_type] || 'default'}>
                    {getActionTypeInfo(item.action_type)?.display_name || item.action_type}
                  </Tag>
                </td>
                <td className="px-4 py-3 border-b">
                  {item.screen_name ? <Tag color="blue">{item.screen_name}</Tag> : '-'}
                </td>
                <td className="px-4 py-3 border-b">{item.element_name || '-'}</td>
                <td className="px-4 py-3 border-b">
                  {item.action_value ? (
                    item.action_value.length > 30 ? (
                      <Tooltip title={item.action_value}>
                        <span>{item.action_value.substring(0, 30)}...</span>
                      </Tooltip>
                    ) : (
                      <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{item.action_value}</span>
                    )
                  ) : '-'}
                </td>
                <td className="px-4 py-3 border-b">{item.wait_time ? `${item.wait_time}ms` : '-'}</td>
                <td className="px-4 py-3 border-b">
                  <Tooltip title={item.continue_on_error ? "此步骤失败后会继续执行后续步骤" : "此步骤失败后会中断流程"}>
                    <Tag color={item.continue_on_error ? 'orange' : 'default'} style={{ cursor: 'help' }}>
                      {item.continue_on_error ? '✓ 继续' : '✗ 停止'}
                    </Tag>
                  </Tooltip>
                </td>
                <td className="px-4 py-3 border-b">
                  {item.description ? (
                    <Tooltip title={item.description}>
                      <span className="inline-block max-w-[180px] truncate">{item.description}</span>
                    </Tooltip>
                  ) : <span style={{ color: '#bfbfbf' }}>-</span>}
                </td>
                <td className="px-4 py-3 border-b text-sm text-gray-500">
                  {new Date(item.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3 border-b">
                  <Space size="small">
                    <Tooltip title="编辑">
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleModalOpen(item)}
                      />
                    </Tooltip>
                    <Tooltip title="复制">
                      <Button
                        type="text"
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => {
                          const copied = { ...item };
                          delete (copied as any).id;
                          handleModalOpen(copied as any);
                        }}
                      />
                    </Tooltip>
                    <Popconfirm
                      title="确认删除"
                      description={`确定要删除步骤 "${item.name}" 吗？此操作不可恢复。`}
                      onConfirm={() => handleDelete(item.id)}
                      okText="确认"
                      cancelText="取消"
                    >
                      <Tooltip title="删除">
                        <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                      </Tooltip>
                    </Popconfirm>
                  </Space>
                </td>
              </tr>
            )}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={items}
            loading={isLoading}
            rowKey="id"
            scroll={{ x: 1400 }}
            pagination={{
              current: page,
              pageSize: pageSize,
              total: totalSteps,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (newPage, newPageSize) => {
                setPage(newPage);
                setPageSize(newPageSize || 20);
              },
            }}
          />
        )}
      </Card>

      {/* 新建/编辑工作台 */}
      <Drawer
        title={editingStep ? `编辑步骤 · ${editingStep.name}` : '新建步骤'}
        open={isModalVisible}
        onClose={handleModalClose}
        width="64vw"
        destroyOnClose
        extra={
          <Space>
            <Button onClick={handleModalClose}>取消</Button>
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
            message="先选操作类型，再补目标元素/操作值，表单会按操作类型自动收敛字段。"
          />
          <Divider orientation="left">基础信息</Divider>
          <Form.Item
            label="步骤名称"
            name="name"
            rules={[{ required: true, message: '请输入步骤名称' }]}
          >
            <Input placeholder="例如: 点击登录按钮" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="步骤描述" />
          </Form.Item>

          <Form.Item label="AI辅助">
            <Form.Item noStyle shouldUpdate={(prevValues, nextValues) => {
              return prevValues.name !== nextValues.name ||
                     prevValues.action_type !== nextValues.action_type ||
                     prevValues.element_id !== nextValues.element_id;
            }}>
              {({ getFieldValue }) => {
                const elementId = getFieldValue('element_id');
                const element = elementsList.find((e: Element) => e.id === elementId);

                return (
                  <AIDescription
                    type="step"
                    data={{
                      step_name: getFieldValue('name') || '',
                      action_type: getFieldValue('action_type') || '',
                      element_name: element?.name,
                      element_description: element?.description,
                    }}
                    onDescriptionGenerated={(description) => {
                      form.setFieldValue('description', description);
                    }}
                    disabled={!getFieldValue('name') || !getFieldValue('action_type')}
                  />
                );
              }}
            </Form.Item>
          </Form.Item>

          <Form.Item
            label="所属界面"
            name="screen_id"
            rules={[{ required: true, message: '请选择所属界面' }]}
          >
            <DrawerSelector
              placeholder="请选择界面"
              options={screensList.map((screen: Screen) => ({
                value: screen.id,
                label: screen.name,
                description: `${screen.element_count} 个元素`,
              }))}
              value={selectedScreen}
              onChange={(value) => {
                setSelectedScreen(value);
                form.setFieldsValue({ screen_id: value });
              }}
              loading={screensLoading}
              drawerWidth={400}
              placement="right"
            />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.action_type !== currentValues.action_type}>
            {({ getFieldValue }) => {
              const actionType = getFieldValue('action_type');
              const actionInfo = getActionTypeInfo(actionType);
              const configSchema = actionInfo?.config_schema || {};
              const valueFormat = configSchema.value_format || '';
              const valueExample = configSchema.value_example || '';
              const valueDescription = configSchema.value_description || '';

              // 操作详细说明内容
              const actionDetailContent = (
                <div style={{ maxWidth: 400 }}>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong style={{ fontSize: 14 }}>操作名称：</Text>
                    <span>{actionInfo?.display_name || actionType || '-'}</span>
                  </div>
                  {actionInfo?.description && (
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>操作说明：</Text>
                      <div style={{ marginLeft: 8, color: '#666' }}>{actionInfo.description}</div>
                    </div>
                  )}
                  {actionInfo?.category && (
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>所属分类：</Text>
                      <Tag color={ACTION_TYPE_COLORS[actionType] || 'default'} style={{ marginLeft: 8 }}>
                        {actionInfo.category}
                      </Tag>
                    </div>
                  )}
                  {valueFormat && (
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>参数格式：</Text>
                      <code style={{ marginLeft: 8, background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 }}>
                        {valueFormat}
                      </code>
                    </div>
                  )}
                  {valueExample && (
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>参数示例：</Text>
                      <code style={{ marginLeft: 8, background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 }}>
                        {valueExample}
                      </code>
                    </div>
                  )}
                  {valueDescription && (
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>参数说明：</Text>
                      <div style={{ marginLeft: 8, color: '#666', fontSize: 12 }}>{valueDescription}</div>
                    </div>
                  )}
                  {actionInfo?.requires_element && (
                    <div style={{ color: '#1890ff', fontSize: 12 }}>
                      💡 此操作需要选择目标元素
                    </div>
                  )}
                  {actionInfo?.requires_value && (
                    <div style={{ color: '#1890ff', fontSize: 12 }}>
                      💡 此操作需要填写操作值
                    </div>
                  )}
                </div>
              );

              return (
                <Form.Item
                  label={
                    <Space>
                      <span>操作类型</span>
                      {actionType && (
                        <Popover
                          content={actionDetailContent}
                          title="操作详细说明"
                          trigger="click"
                          placement="right"
                          overlayStyle={{ maxWidth: 500 }}
                        >
                          <QuestionCircleOutlined
                            style={{ color: '#1890ff', cursor: 'pointer', fontSize: 14 }}
                          />
                        </Popover>
                      )}
                    </Space>
                  }
                  name="action_type"
                  rules={[{ required: true, message: '请选择操作类型' }]}
                >
            <DrawerSelector
              placeholder="请选择操作类型"
              options={Object.entries(ACTION_TYPE_CATEGORIES).flatMap(([category, types]) =>
                types.map((type) => {
                  const actionInfo = getActionTypeInfo(type);
                  const displayName = actionInfo?.display_name || type;
                  const description = actionInfo?.description || category;
                  const configSchema = actionInfo?.config_schema || {};
                  const valueFormat = configSchema.value_format || '';
                  const valueExample = configSchema.value_example || '';
                  const valueDescription = configSchema.value_description || '';

                  return {
                    value: type,
                    label: displayName,
                    description: (
                      <div>
                        <div>{description}</div>
                        {valueFormat && (
                          <div style={{ fontSize: '12px', color: '#888', marginTop: 4 }}>
                            <div>格式: <code>{valueFormat}</code></div>
                            {valueExample && <div>示例: <code>{valueExample}</code></div>}
                            {valueDescription && <div style={{ marginTop: 2 }}>{valueDescription}</div>}
                          </div>
                        )}
                      </div>
                    ),
                    extra: <Tag color={ACTION_TYPE_COLORS[type] || 'default'}>{category}</Tag>,
                  };
                })
              )}
              value={currentActionType}
              onChange={(value) => {
                setCurrentActionType(value);
                form.setFieldsValue({ action_type: value });
              }}
              drawerWidth={420}
              placement="right"
            />
                </Form.Item>
              );
            }}
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.action_type !== currentValues.action_type}>
            {({ getFieldValue }) => {
              const actionType = getFieldValue('action_type');
              return (
                <>
                  <Divider orientation="left">执行配置</Divider>
                  {/* call 操作类型：选择流程 */}
                  {actionType === 'call' && (
                    <>
                      <Form.Item
                        label="调用流程"
                        name="flow_id"
                        rules={[{ required: true, message: '请选择要调用的流程' }]}
                      >
                        <DrawerSelector
                          placeholder="请选择流程"
                          options={flowsList.map((flow: any) => ({
                            value: flow.id,
                            label: flow.name,
                            description: `${flow.step_count || 0} 个步骤`,
                          }))}
                          loading={flowsLoading}
                          drawerWidth={420}
                          placement="right"
                        />
                      </Form.Item>
                      <div style={{ color: '#1890ff', fontSize: '12px', marginBottom: 16 }}>
                        💡 流程调用：执行到该步骤时会调用选中的流程，执行完成后继续执行后续步骤
                      </div>
                    </>
                  )}

                  {/* 其他需要元素的操作类型 */}
                  {needsElement(actionType) && actionType !== 'call' && (
                    <Form.Item label="目标元素" name="element_id">
                      <DrawerSelector
                        placeholder="请选择元素"
                        options={elementsList.map((element: Element) => ({
                          value: element.id,
                          label: element.name,
                          description: element.locators?.[0]?.type || '',
                        }))}
                        loading={elementsLoading}
                        drawerWidth={420}
                        placement="right"
                      />
                    </Form.Item>
                  )}

                  {needsActionValue(actionType) && (
                    <>
                      <Form.Item
                        label="操作值"
                        name="action_value"
                        extra={(() => {
                          const actionInfo = getActionTypeInfo(actionType);
                          const configSchema = actionInfo?.config_schema || {};
                          const valueFormat = configSchema.value_format || '';
                          const valueExample = configSchema.value_example || '';
                          const valueDescription = configSchema.value_description || '';

                          if (!valueFormat && !valueExample && !valueDescription) {
                            return null;
                          }

                          return (
                            <div style={{ marginTop: 8, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                              {valueFormat && (
                                <div style={{ marginBottom: 4 }}>
                                  <Text strong>参数格式：</Text>
                                  <code style={{ marginLeft: 8, background: '#fff', padding: '2px 6px', borderRadius: 3 }}>
                                    {valueFormat}
                                  </code>
                                </div>
                              )}
                              {valueExample && (
                                <div style={{ marginBottom: 4 }}>
                                  <Text strong>参数示例：</Text>
                                  <code style={{ marginLeft: 8, background: '#fff', padding: '2px 6px', borderRadius: 3 }}>
                                    {valueExample}
                                  </code>
                                </div>
                              )}
                              {valueDescription && (
                                <div style={{ color: '#666', fontSize: '12px' }}>
                                  <Text strong style={{ color: '#333' }}>说明：</Text>
                                  {valueDescription}
                                </div>
                              )}
                            </div>
                          );
                        })()}
                      >
                        <Input
                          placeholder={(() => {
                            const actionInfo = getActionTypeInfo(actionType);
                            const configSchema = actionInfo?.config_schema || {};
                            const valueExample = configSchema.value_example || '';
                            return valueExample || `请输入${actionInfo?.display_name || actionType}的参数值`;
                          })()}
                        />
                      </Form.Item>
                    </>
                  )}

                  {isAssertionType(actionType) && (
                    <Form.Item label="断言配置" name="assertions">
                      <Input placeholder="断言配置（JSON格式）" />
                    </Form.Item>
                  )}

                  {actionType === 'wait_time' && (
                    <Form.Item label="等待时间（毫秒）" name="wait_time">
                      <InputNumber min={0} max={60000} style={{ width: '100%' }} placeholder="例如: 1000" />
                    </Form.Item>
                  )}

                  {!isAssertionType(actionType) && actionType !== 'wait_time' && (
                    <Form.Item label="等待时间（可选）" name="wait_time">
                      <InputNumber min={0} max={60000} style={{ width: '100%' }} placeholder="步骤执行后等待时间" />
                    </Form.Item>
                  )}
                </>
              );
            }}
          </Form.Item>

          <Form.Item
            label="失败继续执行"
            name="continue_on_error"
            valuePropName="checked"
            tooltip="启用后，此步骤失败不会中断流程，会继续执行后续步骤（适用于清理步骤）"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <div style={{ color: '#8c8c8c', fontSize: '12px', marginTop: '-8px' }}>
            💡 提示：不同操作类型可能需要配置不同的参数
          </div>
        </Form>
      </Drawer>
    </div>
  );
};

export default Steps;
