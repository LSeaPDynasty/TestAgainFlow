import React from 'react';
import { Tag } from 'antd';
import type { TagProps } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, ClockCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { cn } from '../../lib/utils';

export type StatusType = 'success' | 'error' | 'loading' | 'pending' | 'warning' | 'default';

export interface StatusTagProps extends Omit<TagProps, 'color' | 'icon'> {
  status: StatusType;
  text?: string;
}

const statusConfig = {
  success: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    className: 'bg-green-50 border-green-200 text-green-700',
  },
  error: {
    color: 'error',
    icon: <CloseCircleOutlined />,
    className: 'bg-red-50 border-red-200 text-red-700',
  },
  loading: {
    color: 'processing',
    icon: <SyncOutlined spin />,
    className: 'bg-blue-50 border-blue-200 text-blue-700',
  },
  pending: {
    color: 'default',
    icon: <ClockCircleOutlined />,
    className: 'bg-gray-50 border-gray-200 text-gray-700',
  },
  warning: {
    color: 'warning',
    icon: <ExclamationCircleOutlined />,
    className: 'bg-orange-50 border-orange-200 text-orange-700',
  },
  default: {
    color: 'default',
    icon: null,
    className: 'bg-gray-50 border-gray-200 text-gray-700',
  },
};

/**
 * Status tag component with predefined status types
 * Automatically applies appropriate colors and icons
 */
export const StatusTag: React.FC<StatusTagProps> = ({
  status,
  text,
  className,
  ...props
}) => {
  const config = statusConfig[status];

  return (
    <Tag
      icon={config.icon}
      className={cn('border font-medium', config.className, className)}
      {...props}
    >
      {text || status.charAt(0).toUpperCase() + status.slice(1)}
    </Tag>
  );
};

export default StatusTag;
