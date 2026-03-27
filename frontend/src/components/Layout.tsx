import React, { type ReactNode } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import RightDrawer from './RightDrawer';
import LogPanel from './LogPanel';
import { useAppStore } from '../store/appStore';

interface LayoutProps {
  children?: ReactNode;
}

const Layout: React.FC<LayoutProps> = () => {
  const { rightDrawerVisible, rightDrawerContent, closeRightDrawer, logPanelVisible } = useAppStore();

  return (
    <div className="layout-container">
      {/* 固定在顶部的 Header */}
      <div className="layout-header">
        <Header />
      </div>

      {/* 主体区域：包含 Sidebar 和 Content */}
      <div className="layout-body">
        {/* 固定的 Sidebar */}
        <div className="layout-sidebar">
          <Sidebar />
        </div>

        {/* 可独立滚动的内容区域 */}
        <div className={`layout-content ${logPanelVisible ? 'with-log-panel' : ''}`}>
          <Outlet />
        </div>
      </div>

      {/* 右侧抽屉 */}
      <RightDrawer
        visible={rightDrawerVisible}
        content={rightDrawerContent}
        onClose={closeRightDrawer}
      />

      {/* 底部日志面板 */}
      <LogPanel />
    </div>
  );
};

export default Layout;
