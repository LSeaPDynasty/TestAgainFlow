import React from 'react';
import { Button as AntButton } from 'antd';
import type { ButtonProps as AntButtonProps } from 'antd';
import { cn } from '../../lib/utils';

export interface ButtonProps extends Omit<AntButtonProps, 'size'> {
  variant?: 'primary' | 'default' | 'dashed' | 'text' | 'link';
  size?: 'small' | 'medium' | 'large';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

/**
 * Enhanced Button component wrapping Ant Design Button
 * Adds additional features like icons and full width
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  children,
  ...props
}) => {
  const sizeMap = {
    small: 'small' as const,
    medium: 'middle' as const,
    large: 'large' as const,
  };

  return (
    <AntButton
      type={variant === 'default' ? undefined : variant}
      size={sizeMap[size]}
      className={cn(
        'transition-all duration-200',
        fullWidth && 'w-full',
        className
      )}
      {...props}
    >
      {leftIcon && <span className="mr-2">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="ml-2">{rightIcon}</span>}
    </AntButton>
  );
};

export default Button;
