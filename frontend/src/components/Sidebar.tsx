import React from 'react';
import { Menu } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppstoreOutlined,
  BlockOutlined,
  CloudServerOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  FolderOutlined,
  HistoryOutlined,
  LaptopOutlined,
  ProjectOutlined,
  ScheduleOutlined,
  TagOutlined,
  TeamOutlined,
  TransactionOutlined,
  CalendarOutlined,
  ExperimentOutlined,
  MobileOutlined,
  BranchesOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { useAppStore } from '../store/appStore';
import './Layout.css';

type MenuItem = {
  key: string;
  icon: React.ReactNode;
  label: string;
  path: string;
  badge?: string | number;
};

type MenuSection = {
  label: string;
  items: MenuItem[];
};

// 导航分组
const menuSections: MenuSection[] = [
  {
    label: '资源管理',
    items: [
      { key: 'screens', icon: <MobileOutlined />, label: '界面', path: '/screens' },
      { key: 'elements', icon: <AppstoreOutlined />, label: '元素', path: '/elements' },
      { key: 'steps', icon: <BlockOutlined />, label: '步骤', path: '/steps' },
      { key: 'flows', icon: <BranchesOutlined />, label: '流程', path: '/flows' },
      { key: 'testcases', icon: <FileTextOutlined />, label: '用例', path: '/testcases' },
      { key: 'suites', icon: <FolderOutlined />, label: '套件', path: '/suites' },
    ],
  },
  {
    label: '执行中心',
    items: [
      { key: 'runs', icon: <PlayCircleOutlined />, label: '执行', path: '/runs' },
      { key: 'history', icon: <HistoryOutlined />, label: '历史', path: '/history' },
      { key: 'scheduled-jobs', icon: <CalendarOutlined />, label: '定时任务', path: '/scheduled-jobs' },
    ],
  },
  {
    label: '配置',
    items: [
      { key: 'devices', icon: <CloudServerOutlined />, label: '设备', path: '/devices' },
      { key: 'profiles', icon: <DatabaseOutlined />, label: '环境', path: '/profiles' },
      { key: 'projects', icon: <ProjectOutlined />, label: '项目', path: '/projects' },
      { key: 'tags', icon: <TagOutlined />, label: '标签', path: '/tags' },
    ],
  },
  {
    label: '系统',
    items: [
      { key: 'dashboard', icon: <DashboardOutlined />, label: '控制台', path: '/' },
      { key: 'test-plans', icon: <ExperimentOutlined />, label: '测试计划', path: '/test-plans' },
      { key: 'users', icon: <TeamOutlined />, label: '用户', path: '/users' },
      { key: 'scheduler', icon: <ScheduleOutlined />, label: '调度器', path: '/scheduler' },
    ],
  },
];

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarCollapsed } = useAppStore();

  const handleMenuClick = ({ key }: { key: string }) => {
    // 查找所有菜单项
    for (const section of menuSections) {
      const item = section.items.find((menuItem) => menuItem.key === key);
      if (item) {
        navigate(item.path);
        return;
      }
    }
  };

  const getSelectedKey = () => {
    const path = location.pathname;
    for (const section of menuSections) {
      const item = section.items.find((menuItem) =>
        path.startsWith(menuItem.path) && menuItem.path !== '/'
      );
      if (item) return item.key;
    }
    return 'dashboard';
  };

  // 生成 Menu items
  const menuItems = menuSections.flatMap((section) => [
    { type: 'group' as const, label: section.label },
    ...section.items.map((item) => ({
      key: item.key,
      icon: item.icon,
      label: item.label,
    })),
  ]);

  return (
    <div className={`layout-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
      {/* Sidebar 头部 */}
      <div className="sidebar-header">
        {!sidebarCollapsed && (
          <span className="sidebar-logo">TestFlow</span>
        )}
      </div>

      {/* Sidebar 菜单 */}
      <Menu
        className="sidebar-menu"
        theme="dark"
        mode="inline"
        selectedKeys={[getSelectedKey()]}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </div>
  );
};

export default Sidebar;
