import React from 'react';
import { Empty } from 'antd';
import { cn } from '../../lib/utils';

export interface EmptyStateProps {
  image?: React.ReactNode | string;
  imageStyle?: React.CSSProperties;
  description?: React.ReactNode;
  className?: string;
}

/**
 * Empty state component for displaying empty content
 * Wraps Ant Design Empty component with additional styling options
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  image,
  imageStyle,
  description = '暂无数据',
  className,
}) => {
  return (
    <div className={cn('flex items-center justify-center py-12', className)}>
      <Empty
        image={image}
        imageStyle={imageStyle}
        description={description}
      />
    </div>
  );
};

export default EmptyState;
