import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MobileOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { Modal, List, Tag, Space } from 'antd';

interface Device {
  id: number;
  serial: string;
  name: string;
  status: string;
}

interface DeviceStatusCardProps {
  online: number;
  total: number;
  devices: Device[];
}

export const DeviceStatusCard: React.FC<DeviceStatusCardProps> = ({ online, total, devices }) => {
  const navigate = useNavigate();
  const [modalVisible, setModalVisible] = useState(false);

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'online':
        return {
          icon: <CheckCircleOutlined />,
          color: 'success',
          text: '在线',
        };
      case 'offline':
        return {
          icon: <CloseCircleOutlined />,
          color: 'default',
          text: '离线',
        };
      case 'unauthorized':
        return {
          icon: <WarningOutlined />,
          color: 'warning',
          text: '未授权',
        };
      default:
        return {
          icon: <CloseCircleOutlined />,
          color: 'default',
          text: '未知',
        };
    }
  };

  const percentage = total > 0 ? (online / total) * 100 : 0;
  const statusColor = percentage >= 80 ? 'green' : percentage >= 50 ? 'yellow' : 'red';

  return (
    <>
      <div
        className="
          stat-card
          bg-gradient-to-br from-gray-50 to-gray-100
          border border-gray-200
          rounded-xl p-5
          hover:shadow-lg hover:-translate-y-1
          transition-all duration-300
          cursor-pointer
        "
        onClick={() => setModalVisible(true)}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 mb-1">在线设备</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-700">
                {online} / {total}
              </span>
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  percentage >= 80
                    ? 'bg-green-100 text-green-600'
                    : percentage >= 50
                    ? 'bg-yellow-100 text-yellow-600'
                    : 'bg-red-100 text-red-600'
                }`}
              >
                {percentage.toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">点击查看设备详情</p>
          </div>
          <div className="text-3xl transform hover:scale-110 transition-transform duration-300">
            📱
          </div>
        </div>

        {/* 设备状态条 */}
        <div className="flex items-center gap-1 mt-3 h-2">
          {devices.slice(0, 10).map((device) => (
            <div
              key={device.serial}
              className={`
                flex-1 rounded-full transition-all duration-200
                ${
                  device.status === 'online'
                    ? 'bg-green-500'
                    : device.status === 'unauthorized'
                    ? 'bg-yellow-500'
                    : 'bg-gray-300'
                }
              `}
              title={`${device.name} - ${device.status}`}
            />
          ))}
          {devices.length > 10 && (
            <div className="w-6 h-2 rounded-full bg-gray-200 flex items-center justify-center text-xs text-gray-500">
              +{devices.length - 10}
            </div>
          )}
        </div>
      </div>

      {/* 设备详情弹窗 */}
      <Modal
        title={
          <Space>
            <MobileOutlined />
            <span>设备列表</span>
          </Space>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={
          <Space>
            <button
              onClick={() => {
                setModalVisible(false);
                navigate('/devices');
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              管理设备
            </button>
          </Space>
        }
        width={600}
      >
        <List
          dataSource={devices}
          renderItem={(device) => {
            const config = getStatusConfig(device.status);
            return (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    <div
                      className={`
                        w-10 h-10 rounded-lg flex items-center justify-center
                        ${
                          device.status === 'online'
                            ? 'bg-green-50'
                            : device.status === 'unauthorized'
                            ? 'bg-yellow-50'
                            : 'bg-gray-50'
                        }
                      `}
                    >
                      <MobileOutlined
                        className={
                          device.status === 'online'
                            ? 'text-green-500'
                            : device.status === 'unauthorized'
                            ? 'text-yellow-500'
                            : 'text-gray-400'
                        }
                      />
                    </div>
                  }
                  title={
                    <Space>
                      <span className="font-medium">{device.name}</span>
                      <Tag color={config.color}>{config.text}</Tag>
                    </Space>
                  }
                  description={`序列号: ${device.serial}`}
                />
              </List.Item>
            );
          }}
        />
      </Modal>
    </>
  );
};
