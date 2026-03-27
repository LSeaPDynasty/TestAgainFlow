import React from 'react';
import { cn } from '../../lib/utils';

export interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'red';
  chart?: React.ReactNode;
  loading?: boolean;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  trend,
  icon,
  color = 'blue',
  chart,
  loading = false,
  className,
}) => {
  if (loading) {
    return (
      <div className={cn('stat-card', className)}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  const trendPositive = trend?.startsWith('+') || trend?.includes('↑');
  const trendNegative = trend?.startsWith('-') || trend?.includes('↓');

  return (
    <div className={cn('stat-card', className)}>
      {/* Header */}
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        {trend && (
          <span
            className={cn(
              'stat-card-trend',
              trendPositive && 'positive',
              trendNegative && 'negative',
              !trendPositive && !trendNegative && 'text-gray-500'
            )}
          >
            {trend}
          </span>
        )}
      </div>

      {/* Body */}
      <div className="stat-card-body">
        <div className="stat-card-value">{value}</div>
        {icon && (
          <div className={cn('stat-card-icon', color)}>
            {icon}
          </div>
        )}
      </div>

      {/* Chart */}
      {chart && (
        <div className="stat-card-chart">
          {chart}
        </div>
      )}
    </div>
  );
};

export default StatCard;
