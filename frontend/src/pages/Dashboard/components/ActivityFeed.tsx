import React from 'react';
import { CheckCircleOutlined, CloseCircleOutlined, PlayCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';

interface Activity {
  id: number;
  name: string;
  status: 'success' | 'failed' | 'running' | 'pending';
  duration: string;
  time: string;
}

interface ActivityFeedProps {
  activities: Activity[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities }) => {
  const getStatusConfig = (status: Activity['status']) => {
    switch (status) {
      case 'success':
        return {
          icon: <CheckCircleOutlined />,
          bgColor: 'bg-green-50',
          textColor: 'text-green-600',
          borderColor: 'border-green-200',
          label: '成功',
        };
      case 'failed':
        return {
          icon: <CloseCircleOutlined />,
          bgColor: 'bg-red-50',
          textColor: 'text-red-600',
          borderColor: 'border-red-200',
          label: '失败',
        };
      case 'running':
        return {
          icon: <PlayCircleOutlined className="animate-pulse" />,
          bgColor: 'bg-blue-50',
          textColor: 'text-blue-600',
          borderColor: 'border-blue-200',
          label: '运行中',
        };
      default:
        return {
          icon: <ClockCircleOutlined />,
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-500',
          borderColor: 'border-gray-200',
          label: '等待',
        };
    }
  };

  return (
    <div className="space-y-3">
      {activities.map((activity) => {
        const config = getStatusConfig(activity.status);
        return (
          <div
            key={activity.id}
            className={`
              activity-item
              flex items-start gap-3 p-3 rounded-lg
              border ${config.borderColor}
              ${config.bgColor}
              hover:shadow-md transition-all duration-200
              cursor-pointer
            `}
          >
            <div className={`${config.textColor} mt-0.5`}>{config.icon}</div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">{activity.name}</p>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-xs text-gray-500">{activity.time}</span>
                <span className="text-xs text-gray-400">•</span>
                <span className="text-xs text-gray-500">{activity.duration}</span>
              </div>
            </div>
            <span
              className={`
                text-xs px-2 py-1 rounded-full
                ${config.bgColor} ${config.textColor}
                font-medium
              `}
            >
              {config.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};
