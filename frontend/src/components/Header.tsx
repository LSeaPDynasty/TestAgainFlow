import React from 'react';
import { Badge, Button, Dropdown, Space, Typography, Input } from 'antd';
import {
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  PlayCircleOutlined,
  ScheduleOutlined,
  SettingOutlined,
  UserOutlined,
  SearchOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '../store/appStore';
import { useProject } from '../contexts/ProjectContext';
import DrawerSelector from './DrawerSelector';
import { getProjects } from '../services/project';
import { clearAuthSession, getMe, getStoredUser } from '../services/auth';
import { useHotkeys } from '../hooks/useHotkeys';
import './Layout.css';

const { Text } = Typography;

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { sidebarCollapsed, toggleSidebar, selectedDevice } = useAppStore();
  const { selectedProjectId, setSelectedProjectId } = useProject();

  const { data: me } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getMe,
    initialData: getStoredUser() ?? undefined,
    staleTime: 60000,
  });

  const { data: projectsResponse } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await getProjects();
      return res;
    },
  });

  const projects = projectsResponse?.data?.data?.items || [];

  const handleLogout = () => {
    clearAuthSession();
    navigate('/login', { replace: true });
  };

  // 快捷键 Ctrl+K 打开命令面板
  useHotkeys('k', () => {
    alert('命令面板功能开发中...');
  }, { preventDefault: true });

  // 快捷键 Ctrl+/ 聚焦搜索
  useHotkeys('/', () => {
    const input = document.querySelector('.global-search-input') as HTMLInputElement;
    input?.focus();
  }, { preventDefault: true });

  const menuItems = [
    {
      key: 'users',
      icon: <UserOutlined />,
      label: 'Users',
      onClick: () => navigate('/users'),
    },
    {
      key: 'scheduler',
      icon: <ScheduleOutlined />,
      label: 'Scheduler',
      onClick: () => navigate('/scheduler'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout,
    },
  ];

  return (
    <div className="header-container">
      {/* 左侧区域 */}
      <div className="header-left">
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleSidebar}
          style={{ color: '#fff' }}
        />

        <div
          className="header-logo"
          onClick={() => navigate('/')}
        >
          TestFlow
        </div>
      </div>

      {/* 中间区域：搜索 */}
      <Input
        className="global-search-input header-search"
        placeholder="搜索... (Ctrl+/)"
        prefix={<SearchOutlined />}
      />

      {/* 右侧区域：操作 */}
      <div className="header-right">
        {/* 命令面板触发器 */}
        <Button
          type="text"
          icon={<ThunderboltOutlined />}
          onClick={() => alert('命令面板功能开发中... (Ctrl+K)')}
          style={{ color: '#fff' }}
          title="命令面板 (Ctrl+K)"
        />

        {/* 项目选择器 */}
        <DrawerSelector
          value={selectedProjectId}
          onChange={setSelectedProjectId}
          placeholder="选择项目"
          options={projects.map((project: any) => ({
            value: project.id,
            label: project.name,
            description: project.description,
          }))}
          drawerWidth={480}
          placement="right"
        />

        {/* 设备状态 */}
        {selectedDevice ? (
          <Badge
            status={selectedDevice.status === 'online' ? 'success' : 'error'}
            text={<span style={{ color: '#fff' }}>{selectedDevice.name} ({selectedDevice.serial})</span>}
          />
        ) : null}

        {/* 执行中心 */}
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={() => navigate('/runs')}
        >
          Run Center
        </Button>

        {/* 用户菜单 */}
        <Space size={8}>
          <Text style={{ color: '#fff' }}>{me?.username || 'Guest'}</Text>
          <Dropdown menu={{ items: menuItems }} placement="bottomRight">
            <Button
              type="text"
              icon={<SettingOutlined />}
              style={{ color: '#fff' }}
            />
          </Dropdown>
        </Space>
      </div>
    </div>
  );
};

export default Header;
