import React from 'react';
import { Card as AntCard } from 'antd';
import type { CardProps as AntCardProps } from 'antd';
import { cn } from '../../lib/utils';

export interface CardProps extends AntCardProps {
  variant?: 'default' | 'bordered' | 'shadow';
  hoverable?: boolean;
  fullWidth?: boolean;
}

/**
 * Enhanced Card component wrapping Ant Design Card
 * Adds additional variants and utility classes
 */
export const Card: React.FC<CardProps> = ({
  variant = 'default',
  hoverable = false,
  fullWidth = false,
  className,
  children,
  ...props
}) => {
  const variantStyles = {
    default: '',
    bordered: 'border border-gray-200',
    shadow: 'shadow-md',
  };

  return (
    <AntCard
      hoverable={hoverable}
      className={cn(
        'transition-all duration-200',
        variantStyles[variant],
        fullWidth && 'w-full',
        className
      )}
      {...props}
    >
      {children}
    </AntCard>
  );
};

export default Card;
