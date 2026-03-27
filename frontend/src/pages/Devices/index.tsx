import React, { useState } from 'react';
import {
  Card,
  Button,
  Space,
  Input,
  Modal,
  Form,
  message,
  Popconfirm,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
  Badge,
} from 'antd';
import {
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  RocketOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDevices, createDevice, updateDevice, deleteDevice, refreshDevices, testDeviceConnection } from '../../services/device';
import { getExecutorStatus, getExecutorDevices } from '../../services/executor';
import DOMViewer from '../../components/DOMViewer';
import DrawerSelector from '../../components/DrawerSelector';

// 类型定义
type Device = {
  id: number;
  name: string;
  serial: string;
  model?: string;
  os_version?: string;
  status: 'online' | 'offline' | 'unauthorized' | 'unknown';
  connection_type: 'USB' | 'TCP/IP';
  ip_port?: string;
  capabilities?: string[];
  created_at: string;
  updated_at: string;
};

type DeviceCreate = {
  name: string;
  serial: string;
  model?: string;
  os_version?: string;
  connection_type: 'USB' | 'TCP/IP';
  ip_port?: string;
  capabilities?: string[];
};

const Devices: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [domViewerVisible, setDomViewerVisible] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<{ serial: string; name: string } | null>(null);
  const [form] = Form.useForm();

  const queryClient = useQueryClient();

  // 获取执行引擎状态
  const { data: executorData } = useQuery({
    queryKey: ['executor-status'],
    queryFn: () => getExecutorStatus(),
    refetchInterval: 5000, // 每5秒刷新执行引擎状态
  });

  // 获取执行引擎设备信息
  const { data: executorDevicesData } = useQuery({
    queryKey: ['executor-devices'],
    queryFn: () => getExecutorDevices(),
    refetchInterval: 5000,
  });

  // 获取设备列表
  const { data: devicesData, isLoading, refetch } = useQuery({
    queryKey: ['devices', page, pageSize],
    queryFn: () =>
      getDevices({
        page,
        page_size: pageSize,
      }),
    refetchInterval: 10000, // 每10秒自动刷新
  });

  // 刷新设备
  const refreshMutation = useMutation({
    mutationFn: refreshDevices,
    onSuccess: () => {
      message.success('设备列表已刷新');
      setLastRefresh(new Date());
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  // 页面首次加载时自动同步执行器设备到数据库
  React.useEffect(() => {
    const syncDevices = async () => {
      try {
        console.log('Syncing devices from executor...');

        // 1. 获取执行器设备列表
        const executorRes = await getExecutorDevices();
        const executorDevices = executorRes?.data?.data?.devices || [];
        console.log('Executor devices:', executorDevices);

        // 2. 获取数据库设备列表
        const dbRes = await getDevices({ page: 1, page_size: 1000 });
        const dbDevices = dbRes?.data?.data?.items || [];
        const dbSerials = new Set(dbDevices.map((d: any) => d.serial));
        console.log('Database devices:', dbDevices);

        // 3. 找出需要注册的新设备
        const newDevices = executorDevices.filter((d: any) => !dbSerials.has(d.serial));
        console.log('New devices to register:', newDevices);

        // 4. 注册新设备
        for (const device of newDevices) {
          try {
            await createDevice({
              name: device.name || device.serial,
              serial: device.serial,
              model: device.model,
              os_version: device.os_version,
              connection_type: (device.connection_type === 'unknown' ? 'USB' : device.connection_type) as 'USB' | 'TCP/IP',
            });
            console.log(`Registered device: ${device.serial}`);
          } catch (error: any) {
            console.error(`Failed to register device ${device.serial}:`, error);
          }
        }

        if (newDevices.length > 0) {
          message.success(`已同步 ${newDevices.length} 个新设备`);
          queryClient.invalidateQueries({ queryKey: ['devices'] });
        }
      } catch (error) {
        console.error('Failed to sync devices:', error);
      }
    };

    syncDevices();
  }, []);

  // 创建设备
  const createMutation = useMutation({
    mutationFn: createDevice,
    onSuccess: () => {
      message.success('创建成功');
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // 更新设备
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<DeviceCreate> }) =>
      updateDevice(id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 删除设备
  const deleteMutation = useMutation({
    mutationFn: deleteDevice,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 测试设备连接
  const testConnectionMutation = useMutation({
    mutationFn: testDeviceConnection,
    onSuccess: () => {
      message.success('设备连接测试成功');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '连接测试失败');
    },
  });

  const totalDevices = devicesData?.data?.data?.total || 0;
  const devices = devicesData?.data?.data?.items || [];

  const handleModalOpen = (device?: Device) => {
    if (device) {
      setEditingDevice(device);
      form.setFieldsValue(device);
    } else {
      setEditingDevice(null);
      form.resetFields();
    }
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingDevice(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingDevice) {
        updateMutation.mutate({ id: editingDevice.id, data: values });
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

  const handleTestConnection = (serial: string) => {
    testConnectionMutation.mutate(serial);
  };

  const handleRefresh = () => {
    refreshMutation.mutate();
  };

  const handleOpenDomViewer = (device: Device) => {
    setSelectedDevice({
      serial: device.serial,
      name: device.name,
    });
    setDomViewerVisible(true);
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'online':
        return <Tag icon={<CheckCircleOutlined />} color="success">● online</Tag>;
      case 'offline':
        return <Tag icon={<CloseCircleOutlined />} color="error">● offline</Tag>;
      case 'unauthorized':
        return <Tag icon={<WarningOutlined />} color="warning">● unauthorized</Tag>;
      default:
        return <Tag color="default">○ unknown</Tag>;
    }
  };

  const getConnectionTypeTag = (type: string) => {
    return <Tag>{type}</Tag>;
  };

  // 计算距离上次刷新的时间
  const getTimeSinceRefresh = () => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - lastRefresh.getTime()) / 1000);
    if (diff < 60) return `${diff} 秒前`;
    return `${Math.floor(diff / 60)} 分钟前`;
  };

  return (
    <div>
      {/* 执行引擎状态 */}
      {executorData?.data?.data && (
        <Card
          style={{ marginBottom: 16 }}
          title={
            <Space>
              <ThunderboltOutlined />
              <span>执行引擎状态</span>
            </Space>
          }
        >
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="连接状态"
                value={executorData.data.data.connected ? "已连接" : "未连接"}
                valueStyle={{ color: executorData.data.data.connected ? '#3f8600' : '#cf1322' }}
                prefix={executorData.data.data.connected ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="活跃引擎"
                value={executorData.data.data.active_executors || 0}
                suffix="个"
                prefix={<RocketOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="正在使用设备"
                value={executorDevicesData?.data?.data?.in_use_count || 0}
                suffix="个"
                prefix={<ClockCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="活动任务"
                value={executorData.data.data.executors?.[0]?.active_tasks || 0}
                suffix="个"
                prefix={<ThunderboltOutlined />}
              />
            </Col>
          </Row>
        </Card>
      )}

      <Card
        title={
          <Space>
            <span>设备管理</span>
            <span style={{ color: '#8c8c8c', fontSize: '14px' }}>
              共 {totalDevices} 个设备
            </span>
          </Space>
        }
        extra={
          <Space>
            <span style={{ color: '#8c8c8c', fontSize: '12px' }}>
              上次刷新: {getTimeSinceRefresh()}
            </span>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={refreshMutation.isPending}
            >
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleModalOpen()}>
              新建设备
            </Button>
          </Space>
        }
      >
        <Row gutter={[16, 16]}>
          {devices.map((device: Device) => {
            // 检查设备是否正在被执行引擎使用
            const executorDeviceInfo = executorDevicesData?.data?.data?.devices?.find(
              (d: any) => d.serial === device.serial
            );
            const isInUse = executorDeviceInfo?.in_use || false;

            return (
              <Col xs={24} sm={12} md={8} lg={6} key={device.id}>
                <Badge.Ribbon
                  text="使用中"
                  color="green"
                  style={{ display: isInUse ? 'block' : 'none' }}
                >
                  <Card
                    size="small"
                    hoverable
                    style={{ height: '100%', position: 'relative' }}
                    title={
                      <Space>
                        <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                          {device.name}
                        </span>
                        {getStatusTag(device.status)}
                        {isInUse && (
                          <Tag color="green" icon={<RocketOutlined />}>
                            运行中
                          </Tag>
                        )}
                      </Space>
                    }
                    extra={
                      <Space size="small">
                        <Tooltip title="编辑">
                          <Button
                            type="text"
                            size="small"
                            icon={<EditOutlined />}
                            onClick={() => handleModalOpen(device)}
                          />
                        </Tooltip>
                        <Popconfirm
                          title="确认删除"
                          description={`确定要删除设备 "${device.name}" 吗？`}
                          onConfirm={() => handleDelete(device.id)}
                          okText="确认"
                          cancelText="取消"
                          disabled={isInUse}
                        >
                          <Tooltip title={isInUse ? "设备正在使用中，无法删除" : "删除"}>
                            <Button
                              type="text"
                              size="small"
                              danger
                              icon={<DeleteOutlined />}
                              disabled={isInUse}
                            />
                          </Tooltip>
                        </Popconfirm>
                      </Space>
                    }
                  >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div>
                    <div style={{ color: '#8c8c8c', fontSize: '12px' }}>序列号</div>
                    <div style={{ fontFamily: 'monospace', fontSize: '13px' }}>
                      {device.serial}
                    </div>
                  </div>
                  {device.model && (
                    <div>
                      <div style={{ color: '#8c8c8c', fontSize: '12px' }}>型号</div>
                      <div>{device.model}</div>
                    </div>
                  )}
                  {device.os_version && (
                    <div>
                      <div style={{ color: '#8c8c8c', fontSize: '12px' }}>系统版本</div>
                      <div>{device.os_version}</div>
                    </div>
                  )}
                  <div>
                    <div style={{ color: '#8c8c8c', fontSize: '12px' }}>连接类型</div>
                    {getConnectionTypeTag(device.connection_type)}
                  </div>
                  {device.ip_port && (
                    <div>
                      <div style={{ color: '#8c8c8c', fontSize: '12px' }}>IP:端口</div>
                      <div style={{ fontFamily: 'monospace', fontSize: '13px' }}>
                        {device.ip_port}
                      </div>
                    </div>
                  )}
                  {device.status === 'online' && (
                    <>
                      <Button
                        type="primary"
                        size="small"
                        icon={<RocketOutlined />}
                        onClick={() => handleTestConnection(device.serial)}
                        loading={testConnectionMutation.isPending}
                        block
                      >
                        测试连接
                      </Button>
                      <Button
                        size="small"
                        icon={<FileTextOutlined />}
                        onClick={() => handleOpenDomViewer(device)}
                        block
                      >
                        获取DOM
                      </Button>
                    </>
                  )}
                </Space>
              </Card>
            </Badge.Ribbon>
            </Col>
            );
          })}
        </Row>

        {devices.length === 0 && !isLoading && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <p style={{ color: '#8c8c8c' }}>暂无设备，点击"新建设备"开始配置</p>
          </div>
        )}
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingDevice ? `编辑设备 · ${editingDevice.name}` : '新建设备'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleModalClose}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="设备名称"
            name="name"
            rules={[{ required: true, message: '请输入设备名称' }]}
          >
            <Input placeholder="例如: 测试机01" />
          </Form.Item>

          <Form.Item
            label="序列号"
            name="serial"
            rules={[{ required: true, message: '请输入序列号' }]}
          >
            <Input placeholder="例如: emulator-5554" />
          </Form.Item>

          <Form.Item label="型号" name="model">
            <Input placeholder="例如: Pixel 5" />
          </Form.Item>

          <Form.Item label="系统版本" name="os_version">
            <Input placeholder="例如: Android 13" />
          </Form.Item>

          <Form.Item
            label="连接类型"
            name="connection_type"
            initialValue="USB"
            rules={[{ required: true, message: '请选择连接类型' }]}
          >
            <DrawerSelector
              placeholder="请选择连接类型"
              options={[
                { value: 'USB', label: 'USB' },
                { value: 'TCP/IP', label: 'TCP/IP' },
              ]}
              drawerWidth={320}
              placement="right"
            />
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.connection_type !== currentValues.connection_type
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('connection_type') === 'TCP/IP' ? (
                <Form.Item label="IP:端口" name="ip_port">
                  <Input placeholder="例如: 192.168.1.100:5555" />
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Form.Item label="设备能力" name="capabilities">
            <DrawerSelector
              multiple
              placeholder="选择设备能力"
              options={[
                { value: 'biometric', label: '生物识别' },
                { value: 'nfc', label: 'NFC' },
                { value: 'camera', label: '相机' },
              ]}
              drawerWidth={360}
              placement="right"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* DOM查看器 */}
      {selectedDevice && (
        <DOMViewer
          visible={domViewerVisible}
          onClose={() => setDomViewerVisible(false)}
          deviceSerial={selectedDevice.serial}
          deviceName={selectedDevice.name}
        />
      )}
    </div>
  );
};

export default Devices;
