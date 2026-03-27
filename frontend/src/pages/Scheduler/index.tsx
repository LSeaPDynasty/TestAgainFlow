import React, { useMemo } from 'react';
import { Button, Card, Form, InputNumber, Select, Space, Statistic, Switch, Table, Tag, message } from 'antd';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getSchedulerConfig,
  getSchedulerQueueState,
  updateSchedulerConfig,
  type SchedulerConfig,
} from '../../services/scheduler';
import DrawerSelector from '../../components/DrawerSelector';

const SchedulerPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [form] = Form.useForm<SchedulerConfig>();

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['scheduler', 'config'],
    queryFn: getSchedulerConfig,
  });

  const { data: queueState, isLoading: queueLoading } = useQuery({
    queryKey: ['scheduler', 'queue'],
    queryFn: getSchedulerQueueState,
    refetchInterval: 5000,
  });

  const saveMutation = useMutation({
    mutationFn: updateSchedulerConfig,
    onSuccess: () => {
      message.success('Scheduler config updated');
      queryClient.invalidateQueries({ queryKey: ['scheduler'] });
    },
  });

  React.useEffect(() => {
    if (config) {
      form.setFieldsValue(config);
    }
  }, [config, form]);

  const statusRows = useMemo(
    () =>
      Object.entries(queueState?.statuses || {}).map(([taskId, status]) => ({
        taskId,
        status,
      })),
    [queueState?.statuses],
  );

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card
        title="Scheduler Config"
        extra={
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['scheduler'] })}>
            Refresh
          </Button>
        }
        loading={configLoading}
      >
        <Form
          form={form}
          layout="inline"
          onFinish={(values) => saveMutation.mutate(values)}
          initialValues={config}
        >
          <Form.Item name="enabled" label="Enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="max_inflight_tasks" label="Max Inflight" rules={[{ required: true }]}>
            <InputNumber min={1} max={100} />
          </Form.Item>
          <Form.Item name="default_priority" label="Default Priority" rules={[{ required: true }]}>
            <InputNumber min={1} max={10} />
          </Form.Item>
          <Form.Item name="queue_strategy" label="Queue Strategy" rules={[{ required: true }]}>
            <DrawerSelector
              placeholder="Queue Strategy"
              options={[{ label: 'priority', value: 'priority' }]}
              drawerWidth={280}
              placement="right"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={saveMutation.isPending}>
              Save
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Queue State" loading={queueLoading}>
        <Space size={24} style={{ marginBottom: 16 }}>
          <Statistic title="Queued Tasks" value={queueState?.queue_size || 0} />
          <Statistic title="Tracked Tasks" value={statusRows.length} />
        </Space>

        <Table
          rowKey="taskId"
          dataSource={statusRows}
          pagination={{ pageSize: 10 }}
          columns={[
            { title: 'Task ID', dataIndex: 'taskId' },
            {
              title: 'Status',
              dataIndex: 'status',
              render: (value: string) => {
                const color =
                  value === 'running' ? 'processing' : value === 'success' ? 'success' : value === 'failed' ? 'error' : 'default';
                return <Tag color={color}>{value}</Tag>;
              },
            },
          ]}
        />
      </Card>
    </Space>
  );
};

export default SchedulerPage;
