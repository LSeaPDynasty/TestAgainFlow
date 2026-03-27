import React, { useState } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Input,
  Modal,
  Form,
  Select,
  message,
  Popconfirm,
  Drawer,
  Divider,
  List,
  Tag,
  Empty,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  NodeIndexOutlined,
  MinusCircleOutlined,
  PlusOutlined as AddIcon,
  UploadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getScreens, createScreen, updateScreen, deleteScreen } from '../../services/screen';
import { getElements, createElement as createElementApi } from '../../services/element';
import { getProjects, type Project } from '../../services/project';
import BulkImport from '../../components/BulkImport';
import DrawerSelector from '../../components/DrawerSelector';
import { useProject } from '../../contexts/ProjectContext';

// 类型定义
type Screen = {
  id: number;
  name: string;
  description?: string;
  activity?: string;
  project_id?: number;
  element_count: number;
  created_at: string;
  updated_at: string;
};

type ScreenCreate = {
  name: string;
  description?: string;
  project_id?: number;
};

type Element = {
  id: number;
  name: string;
  screen_id: number;
  locators: Array<{
    type: string;
    value: string;
    priority: number;
  }>;
};

const { Search } = Input;
const { Option } = Select;

const Screens: React.FC = () => {
  const { selectedProjectId } = useProject();
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingScreen, setEditingScreen] = useState<Screen | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [elementsDrawerVisible, setElementsDrawerVisible] = useState(false);
  const [selectedScreenForElements, setSelectedScreenForElements] = useState<Screen | null>(null);
  const [quickAddElementVisible, setQuickAddElementVisible] = useState(false);
  const [bulkImportVisible, setBulkImportVisible] = useState(false);
  const [form] = Form.useForm();
  const [quickAddForm] = Form.useForm();

  const queryClient = useQueryClient();

  // 获取项目列表
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects({ page: 1, page_size: 1000 }),
  });

  const projects: Project[] = projectsData?.data?.data?.items || [];

  // 获取界面列表
  const { data: screensData, isLoading } = useQuery({
    queryKey: ['screens', page, pageSize, searchText],
    queryFn: () =>
      getScreens({
        page,
        page_size: pageSize,
        search: searchText || undefined,
      }),
  });

  // 获取选中界面的元素列表
  const { data: elementsData, refetch: refetchElements } = useQuery({
    queryKey: ['elements', selectedScreenForElements?.id],
    queryFn: () => {
      if (!selectedScreenForElements) return { data: { data: { items: [] } } };
      return getElements({ screen_id: selectedScreenForElements.id, page: 1, page_size: 1000 });
    },
    enabled: elementsDrawerVisible,
  });

  // 创建界面
  const createMutation = useMutation({
    mutationFn: createScreen,
    onSuccess: () => {
      message.success('创建成功');
      queryClient.invalidateQueries({ queryKey: ['screens'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // 更新界面
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ScreenCreate> }) => updateScreen(id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['screens'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 删除界面
  const deleteMutation = useMutation({
    mutationFn: deleteScreen,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['screens'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 快速创建元素
  const quickCreateElementMutation = useMutation({
    mutationFn: createElementApi,
    onSuccess: () => {
      message.success('元素创建成功');
      queryClient.invalidateQueries({ queryKey: ['elements', selectedScreenForElements?.id] });
      queryClient.invalidateQueries({ queryKey: ['screens'] });
      setQuickAddElementVisible(false);
      quickAddForm.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  const totalScreens = screensData?.data.data.total || 0;
  const totalElements = screensData?.data.data.items?.reduce((sum: number, s: Screen) => sum + (s.element_count || 0), 0) || 0;
  const items = screensData?.data.data.items || [];

  const handleModalOpen = (screen?: Screen) => {
    if (screen) {
      setEditingScreen(screen);
      form.setFieldsValue(screen);
    } else {
      setEditingScreen(null);
      form.resetFields();
      // 如果有全局选择的项目，设置为默认值
      if (selectedProjectId) {
        form.setFieldsValue({ project_id: selectedProjectId });
      }
    }
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingScreen(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingScreen) {
        updateMutation.mutate({ id: editingScreen.id, data: values });
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

  const handleViewElements = (screen: Screen) => {
    setSelectedScreenForElements(screen);
    setElementsDrawerVisible(true);
  };

  const handleQuickAddElement = () => {
    quickAddForm.setFieldsValue({
      screen_id: selectedScreenForElements?.id,
      locators: [{ type: 'resource-id', value: '', priority: 1 }],
    });
    setQuickAddElementVisible(true);
  };

  const handleQuickAddSubmit = async () => {
    try {
      const values = await quickAddForm.validateFields();
      values.locators = values.locators.filter((l: any) => l.value && l.value.trim());
      if (values.locators.length === 0) {
        message.error('至少需要添加一个定位符');
        return;
      }
      quickCreateElementMutation.mutate(values);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
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
      title: '界面名称',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (name: string, record: Screen) => (
        <a onClick={() => handleViewElements(record)}>{name}</a>
      ),
    },
    {
      title: 'Activity路径',
      dataIndex: 'activity',
      key: 'activity',
      render: (activity: string) => (
        <Tooltip title={activity}>
          <span style={{ fontFamily: 'monospace', color: '#8c8c8c' }}>
            {activity || '-'}
          </span>
        </Tooltip>
      ),
    },
    {
      title: '元素数量',
      dataIndex: 'element_count',
      key: 'element_count',
      render: (count: number) => (
        <Tag color={count > 0 ? 'green' : 'default'}>{count || 0} 个元素</Tag>
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
      width: 240,
      fixed: 'right' as const,
      render: (_: any, record: Screen) => (
        <Space size="small">
          <Tooltip title="查看元素">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewElements(record)}
            >
              查看元素
            </Button>
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
            description={`确定要删除界面 "${record.name}" 吗？此操作不可恢复。`}
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
            <span>界面管理</span>
            <span style={{ color: '#8c8c8c', fontSize: '14px' }}>
              共 {totalScreens} 个界面，共 {totalElements} 个元素
            </span>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<UploadOutlined />} onClick={() => setBulkImportVisible(true)}>
              批量导入
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleModalOpen()}>
              新建界面
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: '16px' }} size="middle">
          <Search
            placeholder="搜索界面名称"
            allowClear
            style={{ width: 200 }}
            onSearch={setSearchText}
            enterButton={<SearchOutlined />}
          />
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ['screens'] })}>
            刷新
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={items}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1000 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: totalScreens,
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

      {/* 新建/编辑工作台 */}
      <Drawer
        title={editingScreen ? `编辑界面 · ${editingScreen.name}` : '新建界面'}
        open={isModalVisible}
        onClose={handleModalClose}
        width="56vw"
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
          <Form.Item
            label="界面名称"
            name="name"
            rules={[{ required: true, message: '请输入界面名称' }]}
          >
            <Input placeholder="例如: LoginScreen" />
          </Form.Item>

          <Form.Item label="所属项目" name="project_id">
            <Select
              placeholder={selectedProjectId ? `已选择全局项目（ID: ${selectedProjectId}）` : "请选择项目"}
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {projects.map((project) => (
                <Option key={project.id} value={project.id}>
                  {project.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <Input.TextArea rows={3} placeholder="界面描述" />
          </Form.Item>
        </Form>
      </Drawer>

      {/* 查看元素抽屉 */}
      <Drawer
        title={`${selectedScreenForElements?.name} - 元素列表`}
        placement="right"
        width={600}
        open={elementsDrawerVisible}
        onClose={() => setElementsDrawerVisible(false)}
        extra={
          <Button type="primary" icon={<AddIcon />} onClick={handleQuickAddElement}>
            快速添加元素
          </Button>
        }
      >
        <List
          dataSource={elementsData?.data?.data?.items || []}
          locale={{ emptyText: <Empty description="暂无元素" /> }}
          renderItem={(element: any) => (
            <List.Item
              key={element.id}
              actions={[
                <Button type="link" size="small">编辑</Button>,
                <Button type="link" size="small" danger>删除</Button>,
              ]}
            >
              <List.Item.Meta
                title={<strong>{element.name}</strong>}
                description={
                  <Space direction="vertical" size="small">
                    <Space wrap>
                      {element.locators?.slice(0, 2).map((locator: any, index: number) => (
                        <Tag key={index} color="blue">
                          [{locator.priority}] {locator.type}: {locator.value}
                        </Tag>
                      ))}
                      {element.locators?.length > 2 && (
                        <Tag>+{element.locators.length - 2}</Tag>
                      )}
                    </Space>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Drawer>

      {/* 快速添加元素弹窗 */}
      <Modal
        title={`快速添加元素 · ${selectedScreenForElements?.name}`}
        open={quickAddElementVisible}
        onOk={handleQuickAddSubmit}
        onCancel={() => {
          setQuickAddElementVisible(false);
          quickAddForm.resetFields();
        }}
        confirmLoading={quickCreateElementMutation.isPending}
        width={640}
        destroyOnClose
      >
        <Form form={quickAddForm} layout="vertical">
          <Form.Item
            name="screen_id"
            hidden
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="元素名称"
            name="name"
            rules={[{ required: true, message: '请输入元素名称' }]}
          >
            <Input placeholder="例如: submitBtn" />
          </Form.Item>

          <Form.Item
            label="定位符"
            name="locators"
            rules={[{ required: true, message: '请至少添加一个定位符' }]}
          >
            <Form.List name="locators">
              {(fields, { add, remove }) => (
                <>
                  {fields.map((field, index) => (
                    <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 8 }}>
                      <Form.Item
                        {...field}
                        name={[field.name, 'type']}
                        rules={[{ required: true, message: '请选择类型' }]}
                      >
                        <DrawerSelector
                          placeholder="类型"
                          options={[
                            { value: 'resource-id', label: 'resource-id' },
                            { value: 'text', label: 'text' },
                            { value: 'xpath', label: 'xpath' },
                            { value: 'id', label: 'id' },
                            { value: 'class', label: 'class' },
                          ]}
                          drawerWidth={320}
                          placement="right"
                        />
                      </Form.Item>
                      <Form.Item
                        {...field}
                        name={[field.name, 'value']}
                        rules={[{ required: true, message: '请输入定位符值' }]}
                      >
                        <Input placeholder="例如: com.app:id/btn" />
                      </Form.Item>
                      <Form.Item
                        {...field}
                        name={[field.name, 'priority']}
                        initialValue={index + 1}
                      >
                        <Input type="number" min={1} max={100} style={{ width: 80 }} placeholder="优先级" />
                      </Form.Item>
                      <MinusCircleOutlined
                        onClick={() => remove(field.name)}
                        style={{ fontSize: 16, color: '#ff4d4f' }}
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

          <div style={{ color: '#8c8c8c', fontSize: '12px', marginTop: '-8px' }}>
            💡 提示：定位符按优先级从高到低依次尝试
          </div>
        </Form>
      </Modal>

      {/* 批量导入 */}
      <BulkImport
        visible={bulkImportVisible}
        onClose={() => setBulkImportVisible(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['screens'] });
        }}
      />
    </div>
  );
};

export default Screens;
