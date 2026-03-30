import React, { useState } from 'react';
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  message,
  Popconfirm,
  Tooltip,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, UserSwitchOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import {
  getProjectMembers,
  addProjectMember,
  updateMemberRole,
  removeProjectMember,
  type ProjectMember,
} from '../../services/permissions';

const ROLE_OPTIONS = [
  { label: '查看者 (Viewer)', value: 'viewer' },
  { label: '编辑者 (Editor)', value: 'editor' },
  { label: '管理员 (Admin)', value: 'admin' },
];

const ROLE_COLORS: Record<string, string> = {
  viewer: 'default',
  editor: 'blue',
  admin: 'orange',
  owner: 'red',
};

const ROLE_LABELS: Record<string, string> = {
  viewer: '查看者',
  editor: '编辑者',
  admin: '管理员',
  owner: '所有者',
};

const ProjectMembersPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  const pid = Number(projectId);

  // 获取项目成员列表
  const { data: members = [], isLoading } = useQuery({
    queryKey: ['projectMembers', pid],
    queryFn: () => getProjectMembers(pid),
    enabled: !!pid,
  });

  // 添加成员
  const addMutation = useMutation({
    mutationFn: (data: { username: string; role: string }) =>
      addProjectMember(pid, { username: data.username, role: data.role as any }),
    onSuccess: () => {
      message.success('成员添加成功');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['projectMembers', pid] });
    },
  });

  // 更新角色
  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: string }) =>
      updateMemberRole(pid, userId, { role: role as any }),
    onSuccess: () => {
      message.success('角色更新成功');
      queryClient.invalidateQueries({ queryKey: ['projectMembers', pid] });
    },
  });

  // 移除成员
  const removeMutation = useMutation({
    mutationFn: (userId: number) => removeProjectMember(pid, userId),
    onSuccess: () => {
      message.success('成员移除成功');
      queryClient.invalidateQueries({ queryKey: ['projectMembers', pid] });
    },
  });

  const handleAddMember = async () => {
    try {
      const values = await form.validateFields();
      addMutation.mutate(values);
    } catch (error) {
      // 表单验证失败
    }
  };

  const handleUpdateRole = (userId: number, newRole: string) => {
    updateRoleMutation.mutate({ userId, role: newRole });
  };

  const handleRemoveMember = (userId: number) => {
    removeMutation.mutate(userId);
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (username: string) => <strong>{username}</strong>,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (email: string | null) => email || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string, record: ProjectMember) => {
        if (role === 'owner') {
          return <Tag color={ROLE_COLORS[role]}>所有者</Tag>;
        }

        return (
          <Select
            value={role}
            style={{ width: 120 }}
            onChange={(newRole) => handleUpdateRole(record.user_id, newRole)}
            disabled={updateRoleMutation.isPending}
          >
            {ROLE_OPTIONS.filter((opt) => opt.value !== 'owner').map((opt) => (
              <Select.Option key={opt.value} value={opt.value}>
                {opt.label}
              </Select.Option>
            ))}
          </Select>
        );
      },
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (date: string | null) => (date ? new Date(date).toLocaleString('zh-CN') : '-'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: ProjectMember) =>
        record.role !== 'owner' && (
          <Popconfirm
            title="确定要移除该成员吗？"
            onConfirm={() => handleRemoveMember(record.user_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              size="small"
              icon={<DeleteOutlined />}
              loading={removeMutation.isPending}
            >
              移除
            </Button>
          </Popconfirm>
        ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <UserSwitchOutlined />
            <span>项目成员管理</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalOpen(true)}
          >
            添加成员
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={members}
          rowKey="id"
          loading={isLoading}
          pagination={false}
        />
      </Card>

      <Modal
        title="添加项目成员"
        open={isModalOpen}
        onOk={handleAddMember}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
        }}
        confirmLoading={addMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入要添加的用户名" />
          </Form.Item>

          <Form.Item
            label="角色"
            name="role"
            initialValue="viewer"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select>
              {ROLE_OPTIONS.map((option) => (
                <Select.Option key={option.value} value={option.value}>
                  {option.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProjectMembersPage;
