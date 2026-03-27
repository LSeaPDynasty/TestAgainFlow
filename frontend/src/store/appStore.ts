import React from 'react';
import { create } from 'zustand';

interface Device {
  id: number;
  serial: string;
  name: string;
  status: string;
  device_type: string;
  os_version: string;
  app_version?: string;
  screen_size: string;
  properties?: Record<string, any>;
  last_online?: string;
  created_at: string;
  updated_at: string;
}

interface AppState {
  // 当前选中的设备
  selectedDevice: Device | null;
  setSelectedDevice: (device: Device | null) => void;

  // 侧边栏折叠状态
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // 右侧抽屉状态
  rightDrawerVisible: boolean;
  rightDrawerContent: React.ReactNode | null;
  openRightDrawer: (content: React.ReactNode) => void;
  closeRightDrawer: () => void;

  // 底部日志面板状态
  logPanelVisible: boolean;
  toggleLogPanel: () => void;

  // 主题
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;

  // 刷新标记
  refreshKey: number;
  triggerRefresh: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedDevice: null,
  setSelectedDevice: (device) => set({ selectedDevice: device }),

  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  rightDrawerVisible: false,
  rightDrawerContent: null,
  openRightDrawer: (content) => set({ rightDrawerVisible: true, rightDrawerContent: content }),
  closeRightDrawer: () => set({ rightDrawerVisible: false, rightDrawerContent: null }),

  logPanelVisible: false,
  toggleLogPanel: () => set((state) => ({ logPanelVisible: !state.logPanelVisible })),

  theme: 'light',
  setTheme: (theme) => set({ theme }),

  refreshKey: 0,
  triggerRefresh: () => set((state) => ({ refreshKey: state.refreshKey + 1 })),
}));
