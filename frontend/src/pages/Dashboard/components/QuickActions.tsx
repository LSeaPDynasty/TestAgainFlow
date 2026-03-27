import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlusOutlined,
  PlayCircleOutlined,
  MobileOutlined,
  SettingOutlined,
  FileTextOutlined,
  BranchesOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';

interface QuickAction {
  icon: React.ReactNode;
  title: string;
  description: string;
  href: string;
  color: string;
}

export const QuickActions: React.FC = () => {
  const navigate = useNavigate();

  const quickActions: QuickAction[] = [
    {
      icon: <FileTextOutlined />,
      title: '创建用例',
      description: '新建测试用例',
      href: '/testcases',
      color: 'blue',
    },
    {
      icon: <PlayCircleOutlined />,
      title: '执行测试',
      description: '运行测试流程',
      href: '/runs',
      color: 'green',
    },
    {
      icon: <MobileOutlined />,
      title: '管理设备',
      description: '配置测试设备',
      href: '/devices',
      color: 'orange',
    },
    {
      icon: <SettingOutlined />,
      title: '环境配置',
      description: '管理测试环境',
      href: '/profiles',
      color: 'purple',
    },
    {
      icon: <BranchesOutlined />,
      title: '流程管理',
      description: '编辑测试流程',
      href: '/flows',
      color: 'cyan',
    },
  ];

  const colorStyles = {
    blue: 'hover:bg-blue-50 hover:border-blue-300 group-hover/blue:bg-blue-100',
    green: 'hover:bg-green-50 hover:border-green-300 group-hover/green:bg-green-100',
    orange: 'hover:bg-orange-50 hover:border-orange-300 group-hover/orange:bg-orange-100',
    purple: 'hover:bg-purple-50 hover:border-purple-300 group-hover/purple:bg-purple-100',
    cyan: 'hover:bg-cyan-50 hover:border-cyan-300 group-hover/cyan:bg-cyan-100',
  };

  const iconColorStyles = {
    blue: 'text-blue-500 bg-blue-50',
    green: 'text-green-500 bg-green-50',
    orange: 'text-orange-500 bg-orange-50',
    purple: 'text-purple-500 bg-purple-50',
    cyan: 'text-cyan-500 bg-cyan-50',
  };

  return (
    <div className="space-y-2">
      {quickActions.map((action) => (
        <button
          key={action.title}
          onClick={() => navigate(action.href)}
          className={`
            w-full text-left
            p-3 rounded-lg
            border border-gray-200
            ${colorStyles[action.color as keyof typeof colorStyles]}
            transition-all duration-200
            group
            hover:shadow-md
          `}
        >
          <div className="flex items-center gap-3">
            <div
              className={`
                w-10 h-10 rounded-lg
                flex items-center justify-center
                ${iconColorStyles[action.color as keyof typeof iconColorStyles]}
                group-hover:scale-110
                transition-transform duration-200
              `}
            >
              {action.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-800 text-sm">{action.title}</div>
              <div className="text-xs text-gray-500 truncate">{action.description}</div>
            </div>
            <ArrowRightOutlined className="text-gray-400 group-hover:text-gray-600 transition-colors" />
          </div>
        </button>
      ))}
    </div>
  );
};
