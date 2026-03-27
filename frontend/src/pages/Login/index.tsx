import React, { useMemo, useState } from 'react';
import { Alert, Button, Card, Form, Input, Segmented, Space, Typography, message } from 'antd';
import { useMutation } from '@tanstack/react-query';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { isAuthenticated, login, register } from '../../services/auth';

const { Title, Text } = Typography;

type Mode = 'login' | 'register';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mode, setMode] = useState<Mode>('login');
  const [form] = Form.useForm();

  const redirectTo = useMemo(() => {
    const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    return from || '/';
  }, [location.state]);

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      message.success('Login success');
      navigate(redirectTo, { replace: true });
    },
  });

  const registerMutation = useMutation({
    mutationFn: register,
    onSuccess: () => {
      message.success('Register success, please login');
      setMode('login');
      form.resetFields(['password', 'email']);
    },
  });

  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (mode === 'login') {
      loginMutation.mutate({ username: values.username, password: values.password });
      return;
    }

    registerMutation.mutate({
      username: values.username,
      password: values.password,
      email: values.email,
      role: 'member',
    });
  };

  const loading = loginMutation.isPending || registerMutation.isPending;
  const error = (loginMutation.error as Error | null)?.message || (registerMutation.error as Error | null)?.message;

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%)',
        padding: 16,
      }}
    >
      <Card style={{ width: 420, maxWidth: '100%' }}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Title level={3} style={{ marginBottom: 0 }}>
              TestFlow
            </Title>
            <Text type="secondary">Automation platform access</Text>
          </div>

          <Segmented
            block
            value={mode}
            onChange={(value) => setMode(value as Mode)}
            options={[
              { label: 'Login', value: 'login' },
              { label: 'Register', value: 'register' },
            ]}
          />

          {error ? <Alert type="error" message={error} showIcon /> : null}

          <Form form={form} layout="vertical" onFinish={handleSubmit}>
            <Form.Item
              label="Username"
              name="username"
              rules={[{ required: true, min: 3, message: 'Enter username (>=3 chars)' }]}
            >
              <Input autoComplete="username" placeholder="Username" />
            </Form.Item>

            <Form.Item
              label="Password"
              name="password"
              rules={[{ required: true, min: 6, message: 'Enter password (>=6 chars)' }]}
            >
              <Input.Password autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
            </Form.Item>

            {mode === 'register' ? (
              <Form.Item label="Email" name="email" rules={[{ type: 'email', message: 'Invalid email' }]}>
                <Input autoComplete="email" placeholder="Optional" />
              </Form.Item>
            ) : null}

            <Button htmlType="submit" type="primary" block loading={loading}>
              {mode === 'login' ? 'Login' : 'Create account'}
            </Button>
          </Form>
        </Space>
      </Card>
    </div>
  );
};

export default LoginPage;
