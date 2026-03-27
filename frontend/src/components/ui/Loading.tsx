import React from 'react';
import { Spin } from 'antd';
import type { SpinProps } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import { cn } from '../../lib/utils';

export interface LoadingProps extends Omit<SpinProps, 'indicator'> {
  size?: 'small' | 'medium' | 'large';
  fullScreen?: boolean;
  text?: string;
}

/**
 * Loading component for displaying loading state
 * Wraps Ant Design Spin component with additional features
 */
export const Loading: React.FC<LoadingProps> = ({
  size = 'medium',
  fullScreen = false,
  text,
  className,
  ...props
}) => {
  const sizeMap = {
    small: 'small' as const,
    medium: 'default' as const,
    large: 'large' as const,
  };

  const indicator = <LoadingOutlined style={{ fontSize: size === 'large' ? 32 : size === 'small' ? 16 : 24 }} spin />;

  const content = (
    <Spin
      indicator={indicator}
      size={sizeMap[size]}
      className={cn(className)}
      {...props}
    >
      {text && <p className="mt-3 text-gray-500">{text}</p>}
    </Spin>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white bg-opacity-75 z-50">
        {content}
      </div>
    );
  }

  return content;
};

export default Loading;
