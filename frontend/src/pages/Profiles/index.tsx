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
  Divider,
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  CopyOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  PlusOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getProfiles,
  createProfile,
  updateProfile,
  deleteProfile,
  type Profile,
  type ProfileCreate,
} from '../../services/profile';

const { Search } = Input;
const { TextArea } = Input;

const Profiles: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const queryClient = useQueryClient();

  // 获取环境配置列表
  const { data: profilesData, isLoading } = useQuery({
    queryKey: ['profiles', page, pageSize, searchText],
    queryFn: () =>
      getProfiles({
        page,
        page_size: pageSize,
        search: searchText || undefined,
      }),
  });

  // 创建环境配置
  const createMutation = useMutation({
    mutationFn: createProfile,
    onSuccess: () => {
      message.success('创建成功');
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // 更新环境配置
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateProfile(id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 删除环境配置
  const deleteMutation = useMutation({
    mutationFn: deleteProfile,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  const totalProfiles = profilesData?.data?.data?.total || 0;
  const items = profilesData?.data?.data?.items || [];

  const handleModalOpen = (profile?: Profile) => {
    if (profile) {
      setEditingProfile(profile);
      // 转换data对象为键值对数组
      const kvPairs = Object.entries(profile.data || {}).map(([env, vars]) => {
        if (typeof vars === 'object') {
          return Object.entries(vars).map(([key, value]) => ({
            env,
            key,
            value,
          }));
        }
        return [];
      }).flat();

      form.setFieldsValue({
        name: profile.name,
        description: profile.description,
        variables: kvPairs.length > 0 ? kvPairs : [{ env: '', key: '', value: '' }],
      });
    } else {
      setEditingProfile(null);
      form.resetFields();
      form.setFieldsValue({
        variables: [{ env: 'common', key: '', value: '' }],
      });
    }
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingProfile(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      // 将键值对数组转换为嵌套对象
      const data: Record<string, Record<string, string>> = {};
      values.variables?.forEach((v: any) => {
        if (v.env && v.key) {
          if (!data[v.env]) {
            data[v.env] = {};
          }
          data[v.env][v.key] = v.value || '';
        }
      });

      const profileData = {
        name: values.name,
        description: values.description,
        data,
      };

      if (editingProfile) {
        updateMutation.mutate({ id: editingProfile.id, data: profileData });
      } else {
        createMutation.mutate(profileData);
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const getVariableCount = (profile: Profile) => {
    let count = 0;
    Object.values(profile.data || {}).forEach(vars => {
      if (typeof vars === 'object') {
        count += Object.keys(vars).length;
      }
    });
    return count;
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
      title: 'Profile名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Profile) => (
        <Space>
          <strong>{name}</strong>
          {record.is_global && <Tag color="blue">全局</Tag>}
        </Space>
      ),
    },
    {
      title: '变量数量',
      key: 'variable_count',
      render: (_: any, record: Profile) => `${getVariableCount(record)} 个变量`,
    },
    {
      title: '环境',
      key: 'environments',
      render: (_: any, record: Profile) => {
        const envs = Object.keys(record.data || {});
        return envs.length > 0 ? (
          <Space size="small" wrap>
            {envs.map(env => (
              <Tag key={env} color="green">{env}</Tag>
            ))}
          </Space>
        ) : '-';
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (description: string) => {
        if (!description) return '-';
        const maxLength = 50;
        return description.length > maxLength ? (
          <Tooltip title={description}>
            <span>{description.substring(0, maxLength)}...</span>
          </Tooltip>
        ) : (
          <span>{description}</span>
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
      render: (_: any, record: Profile) => (
        <Space size="small">
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
            description={`确定要删除环境配置 "${record.name}" 吗？此操作不可恢复。`}
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
            <span>Profile 管理</span>
            <span style={{ color: '#8c8c8c', fontSize: '14px' }}>共 {totalProfiles} 个环境配置</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleModalOpen()}>
            新建 Profile
          </Button>
        }
      >
        {/* 筛选栏 */}
        <Space style={{ marginBottom: '16px' }} size="middle" wrap>
          <Search
            placeholder="搜索Profile名称"
            allowClear
            style={{ width: 240 }}
            onSearch={setSearchText}
            enterButton={<SearchOutlined />}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['profiles'] })}
          >
            刷新
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={items}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: totalProfiles,
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
        title={editingProfile ? `编辑环境配置 · ${editingProfile.name}` : '新建环境配置'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleModalClose}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="Profile名称"
            name="name"
            rules={[{ required: true, message: '请输入Profile名称' }]}
          >
            <Input placeholder="例如: 开发环境" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="环境描述" />
          </Form.Item>

          <Divider orientation={"left" as any}>环境变量</Divider>

          <Form.List name="variables">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item
                      {...restField}
                      name={[name, 'env']}
                      rules={[{ required: true, message: '请输入环境名' }]}
                    >
                      <Input placeholder="环境 (如: common/dev/prod)" style={{ width: 150 }} />
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'key']}
                      rules={[{ required: true, message: '请输入变量名' }]}
                    >
                      <Input placeholder="变量名" style={{ width: 200 }} />
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'value']}
                    >
                      <Input.Password
                        placeholder="变量值"
                        style={{ width: 250 }}
                        iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                      />
                    </Form.Item>
                    <MinusCircleOutlined
                      onClick={() => remove(name)}
                      style={{ fontSize: 16, color: '#ff4d4f' }}
                    />
                  </Space>
                ))}
                <Form.Item>
                  <Button
                    type="dashed"
                    onClick={() => add({ env: 'common', key: '', value: '' })}
                    block
                    icon={<PlusOutlined />}
                  >
                    添加变量
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <div style={{ color: '#8c8c8c', fontSize: '12px', marginTop: '-8px' }}>
            💡 提示：支持多环境配置，如 common、dev、test、prod 等
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default Profiles;
