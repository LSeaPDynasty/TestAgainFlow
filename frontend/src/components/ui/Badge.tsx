import React from 'react';
import { Badge as AntBadge } from 'antd';
import type { BadgeProps as AntBadgeProps } from 'antd';
import { cn } from '../../lib/utils';

export interface BadgeProps extends Omit<AntBadgeProps, 'count'> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'small' | 'medium' | 'large';
}

/**
 * Enhanced Badge component wrapping Ant Design Badge
 * Adds additional color variants
 */
export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'medium',
  className,
  children,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-orange-100 text-orange-800',
    error: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
  };

  const sizeStyles = {
    small: 'text-xs px-2 py-0.5',
    medium: 'text-sm px-2.5 py-1',
    large: 'text-base px-3 py-1.5',
  };

  if (children) {
    return (
      <AntBadge
        className={cn(className)}
        {...props}
      >
        {children}
      </AntBadge>
    );
  }

  // Standalone badge (count display)
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-full font-medium',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {props.count}
    </span>
  );
};

export default Badge;
