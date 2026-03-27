import React, { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  DatePicker,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProjects, createProject, updateProject, deleteProject, type Project } from '../../services/project';
import dayjs from 'dayjs';
import DrawerSelector from '../../components/DrawerSelector';

const { TextArea } = Input;

const Projects: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();
  const [selectedPriority, setSelectedPriority] = useState<string | undefined>();
  const [searchText, setSearchText] = useState<string>('');

  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [form] = Form.useForm();

  // 获取项目列表
  const { data: projectsData, isLoading } = useQuery({
    queryKey: ['projects', page, pageSize, selectedStatus, selectedPriority, searchText],
    queryFn: () =>
      getProjects({
        page,
        page_size: pageSize,
        status: selectedStatus,
        priority: selectedPriority,
        search: searchText || undefined,
      }),
  });

  const totalProjects = projectsData?.data?.data?.total || 0;
  const items = projectsData?.data?.data?.items || [];

  // 创建项目
  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      message.success('项目创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // 更新项目
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateProject(id, data),
    onSuccess: () => {
      message.success('项目更新成功');
      setEditModalVisible(false);
      setEditingProject(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 删除项目
  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      message.success('项目删除成功');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  const handleCreate = () => {
    form.validateFields().then((values) => {
      const data = {
        ...values,
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : undefined,
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : undefined,
      };
      createMutation.mutate(data);
    });
  };

  const handleEdit = (record: Project) => {
    setEditingProject(record);
    form.setFieldsValue({
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : undefined,
      end_date: record.end_date ? dayjs(record.end_date) : undefined,
    });
    setEditModalVisible(true);
  };

  const handleUpdate = () => {
    if (!editingProject) return;

    form.validateFields().then((values) => {
      const data = {
        ...values,
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : undefined,
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : undefined,
      };
      updateMutation.mutate({ id: editingProject.id, data });
    });
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const getStatusTag = (status: string) => {
    const config = {
      active: { color: 'green', text: '活跃' },
      archived: { color: 'default', text: '已归档' },
      closed: { color: 'red', text: '已关闭' },
    };
    const cfg = config[status as keyof typeof config] || { color: 'default', text: status };
    return <Tag color={cfg.color}>{cfg.text}</Tag>;
  };

  const getPriorityTag = (priority: string) => {
    const config = {
      low: { color: 'default', text: '低' },
      medium: { color: 'blue', text: '中' },
      high: { color: 'orange', text: '高' },
      urgent: { color: 'red', text: '紧急' },
    };
    const cfg = config[priority as keyof typeof config] || { color: 'default', text: priority };
    return <Tag color={cfg.color}>{cfg.text}</Tag>;
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      width: 250,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => getPriorityTag(priority),
    },
    {
      title: '用例数',
      key: 'testcase_count',
      width: 100,
      render: (_: any, record: Project) => record.statistics?.testcase_count || 0,
    },
    {
      title: '套件数',
      key: 'suite_count',
      width: 100,
      render: (_: any, record: Project) => record.statistics?.suite_count || 0,
    },
    {
      title: '执行次数',
      key: 'run_count',
      width: 100,
      render: (_: any, record: Project) => record.statistics?.run_count || 0,
    },
    {
      title: '通过率',
      key: 'pass_rate',
      width: 100,
      render: (_: any, record: Project) => {
        const rate = record.statistics?.pass_rate || 0;
        return <Tag color={rate >= 80 ? 'green' : rate >= 60 ? 'orange' : 'red'}>{rate}%</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => date ? new Date(date).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: Project) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => window.location.href = `#/projects/${record.id}`}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个项目吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="项目管理"
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => queryClient.invalidateQueries({ queryKey: ['projects'] })}
            >
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
              创建项目
            </Button>
          </Space>
        }
      >
        {/* 筛选栏 */}
        <Space style={{ marginBottom: 16 }} size="middle">
          <DrawerSelector
            placeholder="状态筛选"
            options={[
              { value: 'active', label: '活跃' },
              { value: 'archived', label: '已归档' },
              { value: 'closed', label: '已关闭' },
            ]}
            value={selectedStatus}
            onChange={setSelectedStatus}
            drawerWidth={320}
            placement="right"
          />
          <DrawerSelector
            placeholder="优先级筛选"
            options={[
              { value: 'low', label: '低' },
              { value: 'medium', label: '中' },
              { value: 'high', label: '高' },
              { value: 'urgent', label: '紧急' },
            ]}
            value={selectedPriority}
            onChange={setSelectedPriority}
            drawerWidth={320}
            placement="right"
          />
          <Input.Search
            placeholder="搜索项目名称或描述"
            allowClear
            style={{ width: 300 }}
            onSearch={setSearchText}
            enterButton
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
            total: totalProjects,
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

      {/* 创建项目弹窗 */}
      <Modal
        title="创建项目"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <TextArea rows={4} placeholder="请输入项目描述" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="status" label="状态" initialValue="active">
                <DrawerSelector
                  placeholder="请选择状态"
                  options={[
                    { value: 'active', label: '活跃' },
                    { value: 'archived', label: '已归档' },
                    { value: 'closed', label: '已关闭' },
                  ]}
                  drawerWidth={320}
                  placement="right"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="priority" label="优先级" initialValue="medium">
                <DrawerSelector
                  placeholder="请选择优先级"
                  options={[
                    { value: 'low', label: '低' },
                    { value: 'medium', label: '中' },
                    { value: 'high', label: '高' },
                    { value: 'urgent', label: '紧急' },
                  ]}
                  drawerWidth={320}
                  placement="right"
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="start_date" label="开始日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_date" label="结束日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="tags" label="标签">
            <DrawerSelector
              multiple
              placeholder="选择标签"
              options={[
                { value: 'UI测试', label: 'UI测试' },
                { value: 'API测试', label: 'API测试' },
                { value: '性能测试', label: '性能测试' },
                { value: '回归测试', label: '回归测试' },
                { value: '冒烟测试', label: '冒烟测试' },
              ]}
              drawerWidth={360}
              placement="right"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑项目弹窗 */}
      <Modal
        title="编辑项目"
        open={editModalVisible}
        onOk={handleUpdate}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingProject(null);
          form.resetFields();
        }}
        confirmLoading={updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <TextArea rows={4} placeholder="请输入项目描述" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="status" label="状态">
                <DrawerSelector
                  placeholder="请选择状态"
                  options={[
                    { value: 'active', label: '活跃' },
                    { value: 'archived', label: '已归档' },
                    { value: 'closed', label: '已关闭' },
                  ]}
                  drawerWidth={320}
                  placement="right"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="priority" label="优先级">
                <DrawerSelector
                  placeholder="请选择优先级"
                  options={[
                    { value: 'low', label: '低' },
                    { value: 'medium', label: '中' },
                    { value: 'high', label: '高' },
                    { value: 'urgent', label: '紧急' },
                  ]}
                  drawerWidth={320}
                  placement="right"
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="start_date" label="开始日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_date" label="结束日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="tags" label="标签">
            <DrawerSelector
              multiple
              placeholder="选择标签"
              options={[
                { value: 'UI测试', label: 'UI测试' },
                { value: 'API测试', label: 'API测试' },
                { value: '性能测试', label: '性能测试' },
                { value: '回归测试', label: '回归测试' },
                { value: '冒烟测试', label: '冒烟测试' },
              ]}
              drawerWidth={360}
              placement="right"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Projects;
