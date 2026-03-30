import React, { useState } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Input,
  Tag,
  Modal,
  Form,
  message,
  Popconfirm,
  Tooltip,
  Drawer,
  Row,
  Col,
  Divider,
  InputNumber,
  Alert,
  Switch,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  StopOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  PlusCircleOutlined,
  HolderOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getElements, createElement, updateElement, deleteElement, testElementLocator } from '../../services/element';
import { getScreens } from '../../services/screen';
import type { Locator } from '../../services/element';
import DrawerSelector from '../../components/DrawerSelector';
import { VirtualList } from '../../components/ui';
import AIElementDescription from '../../components/AIElementDescription';

// 类型定义
type Element = {
  id: number;
  name: string;
  description?: string;
  screen_id: number;
  screen_name?: string;
  locators: Locator[];
  created_at: string;
  updated_at: string;
};

type ElementCreate = {
  name: string;
  description?: string;
  screen_id: number;
  locators: Locator[];
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

const { Search } = Input;

const LOCATOR_TYPES = [
  'resource-id',
  'text',
  'xpath',
  'id',
  'class',
  'content-desc',
  'accessibility-id',
];

const Elements: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [selectedScreens, setSelectedScreens] = useState<number[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingElement, setEditingElement] = useState<Element | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [testDrawerVisible, setTestDrawerVisible] = useState(false);
  const [testElement, setTestElement] = useState<Element | null>(null);
  const [selectedDeviceSerial, setSelectedDeviceSerial] = useState<string>('');
  const [selectedLocatorIndex, setSelectedLocatorIndex] = useState<number>(0);
  const [testResult, setTestResult] = useState<any>(null);
  const [useVirtualScroll, setUseVirtualScroll] = useState(false);
  const [form] = Form.useForm();

  const queryClient = useQueryClient();

  // 获取元素列表
  const { data: elementsData, isLoading } = useQuery({
    queryKey: ['elements', page, pageSize, searchText, selectedScreens, selectedTypes],
    queryFn: () =>
      getElements({
        page,
        page_size: pageSize,
        search: searchText || undefined,
      }),
  });

  // 获取界面列表（用于筛选）
  const { data: screensData, isLoading: screensLoading, error: screensError } = useQuery({
    queryKey: ['screens-select'],
    queryFn: async () => {
      const response = await getScreens({ page: 1, page_size: 1000 });
      console.log('Screens API response:', response);
      console.log('Response data:', response.data);
      console.log('Response data.data:', response.data?.data);
      console.log('Response data.data.items:', response.data?.data?.items);
      return response;
    },
    staleTime: 60000, // Cache for 1 minute
  });

  // Extract screens list with fallback
  const screensList = screensData?.data?.data?.items || [];
  console.log('Final screensList:', screensList);

  // Log any errors
  if (screensError) {
    console.error('Failed to fetch screens:', screensError);
  }

  // 获取设备列表（用于测试）
  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await fetch('/api/v1/devices');
      const data = await response.json();
      return data.data?.items || [];
    },
    enabled: testDrawerVisible,
  });

  // 创建元素
  const createMutation = useMutation({
    mutationFn: createElement,
    onSuccess: () => {
      message.success('创建成功');
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['screens'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // 更新元素
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateElement(id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['screens'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 删除元素
  const deleteMutation = useMutation({
    mutationFn: deleteElement,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['elements'] });
      queryClient.invalidateQueries({ queryKey: ['screens'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 测试定位符
  const testMutation = useMutation({
    mutationFn: ({ elementId, data }: { elementId: number; data: any }) =>
      testElementLocator(elementId, data),
    onSuccess: (result) => {
      setTestResult(result.data);
    },
    onError: (error: any) => {
      setTestResult({
        found: false,
        error: error.response?.data?.message || '测试失败'
      });
    },
  });

  const handleModalOpen = (element?: Element) => {
    if (element) {
      setEditingElement(element);
      form.setFieldsValue({
        ...element,
        locators: element.locators || [],
      });
    } else {
      setEditingElement(null);
      form.resetFields();
      form.setFieldsValue({ locators: [{ type: 'resource-id', value: '', priority: 1 }] });
    }
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingElement(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      // 过滤掉空定位符
      values.locators = values.locators.filter((l: Locator) => l.value && l.value.trim());
      if (values.locators.length === 0) {
        message.error('至少需要添加一个定位符');
        return;
      }
      if (editingElement) {
        updateMutation.mutate({ id: editingElement.id, data: values });
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

  const handleTest = (element: Element) => {
    setTestElement(element);
    setSelectedLocatorIndex(0);
    setTestResult(null);
    setTestDrawerVisible(true);
    // 默认选择第一个在线设备
    if (devicesData && devicesData.length > 0) {
      const firstOnline = devicesData.find((d: any) => d.status === 'online');
      if (firstOnline) {
        setSelectedDeviceSerial(firstOnline.serial);
      }
    }
  };

  const runTest = () => {
    if (!testElement || !selectedDeviceSerial) {
      message.warning('请选择设备');
      return;
    }
    testMutation.mutate({
      elementId: testElement.id,
      data: {
        device_serial: selectedDeviceSerial,
        locator_index: selectedLocatorIndex,
      },
    });
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
      title: '元素名称',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (name: string, record: Element) => (
        <a onClick={() => handleTest(record)}>{name}</a>
      ),
    },
    {
      title: '所属界面',
      dataIndex: 'screen_name',
      key: 'screen_name',
      render: (name: string) => (name ? <Tag color="blue">{name}</Tag> : '-'),
    },
    {
      title: '定位符',
      dataIndex: 'locators',
      key: 'locators',
      render: (locators: Locator[]) => (
        <Space size={4} wrap>
          {locators?.slice(0, 2).map((locator, index) => (
            <Tooltip
              key={index}
              title={
                <div>
                  <div>类型: {locator.type}</div>
                  <div>值: {locator.value}</div>
                  <div>优先级: {locator.priority}</div>
                </div>
              }
            >
              <Tag color="geekblue">{locator.type}</Tag>
            </Tooltip>
          ))}
          {locators?.length > 2 && (
            <Tooltip
              title={
                <div>
                  {locators.slice(2).map((l, i) => (
                    <div key={i}>
                      {l.type}: {l.value}
                    </div>
                  ))}
                </div>
              }
            >
              <Tag>+{locators.length - 2}</Tag>
            </Tooltip>
          )}
        </Space>
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
      sorter: true,
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: Element) => (
        <Space size="small">
          <Tooltip title="测试定位符">
            <Button
              type="text"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleTest(record)}
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
            description={`确定要删除元素 "${record.name}" 吗？此操作不可恢复。`}
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

  const totalElements = elementsData?.data.data.total || 0;
  const items = elementsData?.data.data.items || [];

  return (
    <div>
      <Card
        title={
          <Space>
            <span className="text-base font-medium">元素管理</span>
            <span className="text-gray-500 text-sm">共 {totalElements} 条</span>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title={useVirtualScroll ? "关闭虚拟滚动" : "开启虚拟滚动（大数据量优化）"}>
              <Switch
                checked={useVirtualScroll}
                onChange={(checked) => setUseVirtualScroll(checked)}
                checkedChildren={<ThunderboltOutlined />}
                unCheckedChildren={<ThunderboltOutlined />}
              />
            </Tooltip>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleModalOpen()}>
              新建元素
            </Button>
          </Space>
        }
      >
        {/* 筛选栏 */}
        <Space className="mb-4" size="middle" wrap>
          <Search
            placeholder="搜索元素名称/定位符"
            allowClear
            className="w-60"
            onSearch={setSearchText}
            enterButton={<SearchOutlined />}
          />
          <DrawerSelector
            multiple
            placeholder="所属界面"
            options={screensList.map((screen: Screen) => ({
              value: screen.id,
              label: screen.name,
              description: `${screen.element_count} 个元素`,
            }))}
            value={selectedScreens}
            onChange={setSelectedScreens}
            drawerWidth={400}
            placement="right"
            loading={screensLoading}
          />
          <DrawerSelector
            multiple
            placeholder="定位类型"
            options={LOCATOR_TYPES.map((type) => ({
              value: type,
              label: type,
            }))}
            value={selectedTypes}
            onChange={setSelectedTypes}
            drawerWidth={320}
            placement="right"
          />
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ['elements'] })}>
            刷新
          </Button>
        </Space>

        {useVirtualScroll ? (
          <VirtualList
            items={items}
            height={600}
            itemHeight={55}
            renderItem={(item: Element, index: number) => (
              <div
                key={item.id}
                className="flex items-center border-b border-gray-200 hover:bg-gray-50 px-4 py-3"
              >
                <div className="w-20 text-gray-500 font-mono text-sm">
                  {(index + 1).toString().padStart(2, '0')}
                </div>
                <div className="flex-1 min-w-0">
                  <a onClick={() => handleTest(item)} className="text-primary-600 hover:text-primary-700 font-medium">
                    {item.name}
                  </a>
                  <div className="flex items-center gap-2 mt-1">
                    {item.screen_name && <Tag color="blue">{item.screen_name}</Tag>}
                    <Space size={4} wrap>
                      {item.locators?.slice(0, 2).map((locator, idx) => (
                        <Tag key={idx} color="geekblue">{locator.type}</Tag>
                      ))}
                      {item.locators && item.locators.length > 2 && (
                        <Tag>+{item.locators.length - 2}</Tag>
                      )}
                    </Space>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Space size="small">
                    <Tooltip title="测试定位符">
                      <Button
                        type="text"
                        size="small"
                        icon={<PlayCircleOutlined />}
                        onClick={() => handleTest(item)}
                      />
                    </Tooltip>
                    <Tooltip title="编辑">
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleModalOpen(item)}
                      />
                    </Tooltip>
                    <Popconfirm
                      title="确认删除"
                      description={`确定要删除元素 "${item.name}" 吗？`}
                      onConfirm={() => handleDelete(item.id)}
                      okText="确认"
                      cancelText="取消"
                    >
                      <Tooltip title="删除">
                        <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                      </Tooltip>
                    </Popconfirm>
                  </Space>
                </div>
              </div>
            )}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={items}
            loading={isLoading}
            rowKey="id"
            scroll={{ x: 1200 }}
            pagination={{
              current: page,
              pageSize: pageSize,
              total: totalElements,
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
        title={editingElement ? `编辑元素 · ${editingElement.name}` : '新建元素'}
        open={isModalVisible}
        onClose={handleModalClose}
        width="62vw"
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
            className="mb-3"
            message="建议先填 1 条稳定定位（resource-id），再补备用定位。"
          />
          <Form.Item
            label="元素名称"
            name="name"
            rules={[{ required: true, message: '请输入元素名称' }]}
          >
            <Input placeholder="例如: loginBtn" />
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
              loading={screensLoading}
              drawerWidth={400}
              placement="right"
            />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <Input.TextArea rows={2} placeholder="元素描述" />
          </Form.Item>

          <Form.Item label="AI辅助">
            <Form.Item noStyle shouldUpdate={(prevValues, nextValues) => {
              return prevValues.name !== nextValues.name ||
                     prevValues.screen_id !== nextValues.screen_id ||
                     prevValues.locators !== nextValues.locators;
            }}>
              {({ getFieldValue }) => {
                const screenId = getFieldValue('screen_id');
                const screen = screensList.find((s: Screen) => s.id === screenId);
                return (
                  <AIElementDescription
                    elementName={getFieldValue('name') || ''}
                    screenName={screen?.name || ''}
                    locators={getFieldValue('locators') || []}
                    onDescriptionGenerated={(description) => {
                      form.setFieldValue('description', description);
                    }}
                  />
                );
              }}
            </Form.Item>
          </Form.Item>

          <Form.Item
            label="定位符列表"
            name="locators"
            rules={[{ required: true, message: '请至少添加一个定位符' }]}
          >
            <Form.List name="locators">
              {(fields, { add, remove }) => (
                <>
                  {fields.map((field, index) => (
                    <Space key={field.key} align="baseline" className="flex mb-2">
                      {fields.length > 1 && (
                        <HolderOutlined className="cursor-move text-base" />
                      )}
                      <Form.Item
                        {...field}
                        key={`type-${field.key}`}
                        name={[field.name, 'type']}
                        rules={[{ required: true, message: '请选择类型' }]}
                      >
                        <DrawerSelector
                          placeholder="类型"
                          options={LOCATOR_TYPES.map((type) => ({
                            value: type,
                            label: type,
                          }))}
                          drawerWidth={320}
                          placement="right"
                        />
                      </Form.Item>
                      <Form.Item
                        {...field}
                        key={`value-${field.key}`}
                        name={[field.name, 'value']}
                        rules={[{ required: true, message: '请输入定位符值' }]}
                      >
                        <Input placeholder="定位符值，如: com.app:id/btn" />
                      </Form.Item>
                      <Form.Item
                        {...field}
                        key={`priority-${field.key}`}
                        name={[field.name, 'priority']}
                        initialValue={index + 1}
                      >
                        <InputNumber min={1} max={100} className="w-[90px]" placeholder="优先级" />
                      </Form.Item>
                      <MinusCircleOutlined
                        onClick={() => remove(field.name)}
                        className="text-base text-error"
                      />
                    </Space>
                  ))}
                  <Form.Item>
                    <Button
                      type="dashed"
                      onClick={() => add({ type: 'resource-id', value: '', priority: fields.length + 1 })}
                      block
                      icon={<PlusOutlined />}
                    >
                      添加备用定位符
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
          </Form.Item>

          <div className="text-gray-500 text-xs -mt-2">
            💡 提示：定位符按优先级从高到低依次尝试，可拖拽调整顺序
          </div>
        </Form>
      </Drawer>

      {/* 元素测试抽屉 */}
      <Drawer
        title="元素测试面板"
        placement="right"
        width={480}
        open={testDrawerVisible}
        onClose={() => setTestDrawerVisible(false)}
      >
        {testElement && (
          <div>
            <Divider orientation={"left" as any}>元素信息</Divider>
            <div style={{ marginBottom: 16 }}>
              <div><strong>名称：</strong>{testElement.name}</div>
              <div><strong>所属界面：</strong>{testElement.screen_name}</div>
            </div>

            <Divider orientation={"left" as any}>定位符</Divider>
            <DrawerSelector
              placeholder="选择定位符"
              options={testElement.locators?.map((locator, index) => ({
                value: index,
                label: `[${locator.priority}] ${locator.type}: ${locator.value}`,
                description: `优先级: ${locator.priority}`,
              })) || []}
              value={selectedLocatorIndex}
              onChange={(value) => setSelectedLocatorIndex(value)}
              drawerWidth={480}
              placement="right"
            />

            <Divider orientation={"left" as any}>设备</Divider>
            <DrawerSelector
              placeholder="选择设备"
              options={devicesData?.map((device: any) => ({
                value: device.serial,
                label: device.name,
                extra: (
                  <Tag color={device.status === 'online' ? 'success' : 'error'}>
                    {device.status}
                  </Tag>
                ),
              })) || []}
              value={selectedDeviceSerial}
              onChange={setSelectedDeviceSerial}
              drawerWidth={400}
              placement="right"
            />

            <Button
              type="primary"
              block
              icon={<PlayCircleOutlined />}
              onClick={runTest}
              loading={testMutation.isPending}
              style={{ marginBottom: 24 }}
            >
              测试定位符
            </Button>

            {testResult && (
              <>
                <Divider orientation={"left" as any}>测试结果</Divider>
                {testResult.found !== undefined && (
                  <div style={{ padding: 16, borderRadius: 8, background: testResult.found ? '#f6ffed' : '#fff2f0' }}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {testResult.found ? (
                        <>
                          <Space>
                            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                            <span style={{ color: '#52c41a', fontWeight: 'bold' }}>✓ 元素找到</span>
                          </Space>
                          {testResult.bounds && (
                            <div>
                              <div>坐标: x={testResult.bounds.x}, y={testResult.bounds.y}</div>
                              <div>尺寸: {testResult.bounds.width} × {testResult.bounds.height}</div>
                            </div>
                          )}
                        </>
                      ) : (
                        <Space>
                          <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
                          <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>✗ 未找到元素</span>
                        </Space>
                      )}
                      {testResult.error && (
                        <div style={{ color: '#ff4d4f' }}>{testResult.error}</div>
                      )}
                    </Space>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Elements;
