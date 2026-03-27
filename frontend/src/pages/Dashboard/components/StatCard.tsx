import React from 'react';
import { Progress } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
  color: 'blue' | 'green' | 'orange' | 'purple' | 'cyan' | 'pink';
  trend?: string;
  description?: string;
  showProgress?: boolean;
  progress?: number;
  compact?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  color,
  trend,
  description,
  showProgress,
  progress,
  compact = false,
}) => {
  const colorStyles = {
    blue: {
      bg: 'from-blue-50 to-blue-100',
      border: 'border-blue-200',
      title: 'text-blue-600',
      value: 'text-blue-700',
      progress: '#1677FF',
    },
    green: {
      bg: 'from-green-50 to-green-100',
      border: 'border-green-200',
      title: 'text-green-600',
      value: 'text-green-700',
      progress: '#52C41A',
    },
    orange: {
      bg: 'from-orange-50 to-orange-100',
      border: 'border-orange-200',
      title: 'text-orange-600',
      value: 'text-orange-700',
      progress: '#FAAD14',
    },
    purple: {
      bg: 'from-purple-50 to-purple-100',
      border: 'border-purple-200',
      title: 'text-purple-600',
      value: 'text-purple-700',
      progress: '#722ED1',
    },
    cyan: {
      bg: 'from-cyan-50 to-cyan-100',
      border: 'border-cyan-200',
      title: 'text-cyan-600',
      value: 'text-cyan-700',
      progress: '#13C2C2',
    },
    pink: {
      bg: 'from-pink-50 to-pink-100',
      border: 'border-pink-200',
      title: 'text-pink-600',
      value: 'text-pink-700',
      progress: '#EB2F96',
    },
  };

  const style = colorStyles[color];
  const isPositive = trend?.startsWith('+');
  const isNegative = trend?.startsWith('-');

  return (
    <div
      className={`
        stat-card group
        bg-gradient-to-br ${style.bg}
        border ${style.border}
        rounded-xl p-5
        hover:shadow-lg hover:-translate-y-1
        transition-all duration-300
        ${compact ? 'p-4' : 'p-5'}
      `}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className={`text-sm font-medium ${style.title} mb-1`}>{title}</p>
          <div className="flex items-baseline gap-2">
            <span
              className={`
                ${compact ? 'text-2xl' : 'text-3xl'}
                font-bold ${style.value}
              `}
            >
              {value}
            </span>
            {trend && (
              <span
                className={`
                  text-xs font-medium flex items-center gap-0.5
                  ${isPositive ? 'text-green-600' : isNegative ? 'text-red-500' : 'text-gray-500'}
                `}
              >
                {isPositive ? <ArrowUpOutlined /> : isNegative ? <ArrowDownOutlined /> : null}
                {trend}
              </span>
            )}
          </div>
          {description && (
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          )}
        </div>
        <div
          className="
            text-3xl
            transform group-hover:scale-110
            transition-transform duration-300
          "
        >
          {icon}
        </div>
      </div>

      {showProgress && progress !== undefined && (
        <div className="mt-3">
          <Progress
            percent={Math.round(progress)}
            strokeColor={style.progress}
            trailColor="#E5E7EB"
            size="small"
            strokeWidth={8}
            showInfo={false}
          />
        </div>
      )}
    </div>
  );
};
