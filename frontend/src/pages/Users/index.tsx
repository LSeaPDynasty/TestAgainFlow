import React, { useMemo, useState } from 'react';
import { Button, Card, Form, Input, Radio, Space, Table, Tag, message } from 'antd';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getMe, getUsers, register, type UserInfo } from '../../services/auth';

const UsersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [role, setRole] = useState<'member' | 'admin'>('member');

  const { data: me, isLoading: meLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getMe,
  });

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    enabled: me?.role === 'admin',
  });

  const createMutation = useMutation({
    mutationFn: register,
    onSuccess: () => {
      message.success('User created');
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const columns = useMemo(
    () => [
      { title: 'ID', dataIndex: 'id', width: 80 },
      { title: 'Username', dataIndex: 'username' },
      { title: 'Email', dataIndex: 'email', render: (email?: string) => email || '-' },
      {
        title: 'Role',
        dataIndex: 'role',
        render: (value: string) => <Tag color={value === 'admin' ? 'gold' : 'blue'}>{value}</Tag>,
      },
      {
        title: 'Status',
        dataIndex: 'is_active',
        render: (active: boolean) => <Tag color={active ? 'success' : 'default'}>{active ? 'active' : 'inactive'}</Tag>,
      },
      { title: 'Created At', dataIndex: 'created_at', render: (value: string) => new Date(value).toLocaleString() },
    ],
    [],
  );

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card title="Current User" loading={meLoading}>
        {me ? (
          <Space size={24} wrap>
            <span><strong>ID:</strong> {me.id}</span>
            <span><strong>Username:</strong> {me.username}</span>
            <span><strong>Email:</strong> {me.email || '-'}</span>
            <span><strong>Role:</strong> <Tag color={me.role === 'admin' ? 'gold' : 'blue'}>{me.role}</Tag></span>
          </Space>
        ) : null}
      </Card>

      {me?.role === 'admin' ? (
        <Card title="Create User">
          <Form form={form} layout="inline" onFinish={(values) => createMutation.mutate({ ...values, role })}>
            <Form.Item name="username" rules={[{ required: true, min: 3 }]}>
              <Input placeholder="Username" style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, min: 6 }]}>
              <Input.Password placeholder="Password" style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="email" rules={[{ type: 'email' }]}>
              <Input placeholder="Email (optional)" style={{ width: 220 }} />
            </Form.Item>
            <Form.Item>
              <Radio.Group
                value={role}
                onChange={(e) => setRole(e.target.value as 'member' | 'admin')}
                options={[
                  { label: 'Member', value: 'member' },
                  { label: 'Admin', value: 'admin' },
                ]}
              />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={createMutation.isPending}>Create</Button>
            </Form.Item>
          </Form>
        </Card>
      ) : null}

      <Card title="User List" extra={me?.role !== 'admin' ? 'Admin only' : undefined}>
        <Table<UserInfo>
          rowKey="id"
          dataSource={users || []}
          columns={columns}
          loading={usersLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </Space>
  );
};

export default UsersPage;
