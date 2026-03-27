import React, { useState, useEffect, useCallback } from 'react';
import { Command } from 'cmdk';
import { useNavigate } from 'react-router-dom';
import {
  DashboardOutlined,
  ProjectOutlined,
  AppstoreOutlined,
  BlockOutlined,
  TransactionOutlined,
  FileTextOutlined,
  FolderOutlined,
  CloudServerOutlined,
  HistoryOutlined,
  CalendarOutlined,
  TeamOutlined,
  SearchOutlined,
  PlusOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useHotkeys } from '../../hooks/useHotkeys';

interface CommandItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  action: () => void;
  category: 'navigation' | 'actions' | 'settings';
  keywords?: string[];
}

const commandItems: CommandItem[] = [
  // Navigation
  {
    id: 'nav-dashboard',
    label: 'Dashboard',
    icon: <DashboardOutlined />,
    action: () => window.location.href = '/',
    category: 'navigation',
    keywords: ['home', '控制台', '主页'],
  },
  {
    id: 'nav-projects',
    label: 'Projects',
    icon: <ProjectOutlined />,
    action: () => window.location.href = '/projects',
    category: 'navigation',
    keywords: ['项目'],
  },
  {
    id: 'nav-elements',
    label: 'Elements',
    icon: <AppstoreOutlined />,
    action: () => window.location.href = '/elements',
    category: 'navigation',
    keywords: ['元素', 'element'],
  },
  {
    id: 'nav-steps',
    label: 'Steps',
    icon: <BlockOutlined />,
    action: () => window.location.href = '/steps',
    category: 'navigation',
    keywords: ['步骤', 'step'],
  },
  {
    id: 'nav-flows',
    label: 'Flows',
    icon: <TransactionOutlined />,
    action: () => window.location.href = '/flows',
    category: 'navigation',
    keywords: ['流程', 'flow'],
  },
  {
    id: 'nav-testcases',
    label: 'Testcases',
    icon: <FileTextOutlined />,
    action: () => window.location.href = '/testcases',
    category: 'navigation',
    keywords: ['测试用例', '用例', 'testcase'],
  },
  {
    id: 'nav-suites',
    label: 'Suites',
    icon: <FolderOutlined />,
    action: () => window.location.href = '/suites',
    category: 'navigation',
    keywords: ['套件', 'suite'],
  },
  {
    id: 'nav-devices',
    label: 'Devices',
    icon: <CloudServerOutlined />,
    action: () => window.location.href = '/devices',
    category: 'navigation',
    keywords: ['设备', 'device'],
  },
  {
    id: 'nav-runs',
    label: 'Runs',
    icon: <HistoryOutlined />,
    action: () => window.location.href = '/runs',
    category: 'navigation',
    keywords: ['执行', '运行', 'run'],
  },
  {
    id: 'nav-scheduled-jobs',
    label: 'Scheduled Jobs',
    icon: <CalendarOutlined />,
    action: () => window.location.href = '/scheduled-jobs',
    category: 'navigation',
    keywords: ['定时任务', '调度', 'schedule'],
  },
  {
    id: 'nav-users',
    label: 'Users',
    icon: <TeamOutlined />,
    action: () => window.location.href = '/users',
    category: 'navigation',
    keywords: ['用户', 'user'],
  },

  // Actions
  {
    id: 'action-new-element',
    label: 'New Element',
    icon: <PlusOutlined />,
    action: () => window.location.href = '/elements?action=new',
    category: 'actions',
    keywords: ['新建', '创建', '元素'],
  },
  {
    id: 'action-new-flow',
    label: 'New Flow',
    icon: <PlusOutlined />,
    action: () => window.location.href = '/flows?action=new',
    category: 'actions',
    keywords: ['新建', '创建', '流程'],
  },
  {
    id: 'action-new-testcase',
    label: 'New Testcase',
    icon: <PlusOutlined />,
    action: () => window.location.href = '/testcases?action=new',
    category: 'actions',
    keywords: ['新建', '创建', '测试用例', '用例'],
  },
  {
    id: 'action-search',
    label: 'Global Search',
    icon: <SearchOutlined />,
    action: () => {/* TODO: Implement global search */},
    category: 'actions',
    keywords: ['搜索', '查找', 'search'],
  },

  // Settings
  {
    id: 'settings-users',
    label: 'User Management',
    icon: <TeamOutlined />,
    action: () => window.location.href = '/users',
    category: 'settings',
    keywords: ['用户管理', '设置', 'settings'],
  },
  {
    id: 'settings-devices',
    label: 'Device Management',
    icon: <SettingOutlined />,
    action: () => window.location.href = '/devices',
    category: 'settings',
    keywords: ['设备管理', '设置', 'settings'],
  },
];

export interface CommandPaletteProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  open: controlledOpen,
  onOpenChange,
}) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const [search, setSearch] = useState('');

  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;

  // Toggle command palette with Ctrl+K or Cmd+K
  useHotkeys('k', () => setOpen(!open), { preventDefault: true });

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
        setSearch('');
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [open, setOpen]);

  const handleSelect = useCallback((item: CommandItem) => {
    item.action();
    setOpen(false);
    setSearch('');
  }, [setOpen]);

  const filteredItems = React.useMemo(() => {
    if (!search) return commandItems;

    const searchLower = search.toLowerCase();
    return commandItems.filter((item) => {
      const labelMatch = item.label.toLowerCase().includes(searchLower);
      const keywordsMatch = item.keywords?.some((kw) =>
        kw.toLowerCase().includes(searchLower)
      );
      return labelMatch || keywordsMatch;
    });
  }, [search]);

  const navigationItems = filteredItems.filter((item) => item.category === 'navigation');
  const actionItems = filteredItems.filter((item) => item.category === 'actions');
  const settingsItems = filteredItems.filter((item) => item.category === 'settings');

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command Palette"
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/50"
    >
      <div className="w-full max-w-lg overflow-hidden rounded-lg bg-white shadow-xl">
        <div className="flex items-center border-b px-4">
          <SearchOutlined className="mr-3 text-gray-400" />
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder="Type a command or search..."
            className="flex h-12 w-full rounded-md border-transparent bg-transparent py-3 text-sm outline-none placeholder:text-gray-400"
          />
        </div>

        <Command.List className="max-h-96 overflow-y-auto p-2">
          {filteredItems.length === 0 ? (
            <div className="py-6 text-center text-sm text-gray-500">
              No results found.
            </div>
          ) : (
            <>
              {navigationItems.length > 0 && (
                <Command.Group heading="Navigation" className="mb-2">
                  {navigationItems.map((item) => (
                    <Command.Item
                      key={item.id}
                      onSelect={() => handleSelect(item)}
                      className="flex cursor-pointer items-center rounded-md px-4 py-2 text-sm hover:bg-gray-100 aria-selected:bg-gray-100"
                    >
                      <span className="mr-3 text-gray-500">{item.icon}</span>
                      <span>{item.label}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              )}

              {actionItems.length > 0 && (
                <Command.Group heading="Actions" className="mb-2">
                  {actionItems.map((item) => (
                    <Command.Item
                      key={item.id}
                      onSelect={() => handleSelect(item)}
                      className="flex cursor-pointer items-center rounded-md px-4 py-2 text-sm hover:bg-gray-100 aria-selected:bg-gray-100"
                    >
                      <span className="mr-3 text-gray-500">{item.icon}</span>
                      <span>{item.label}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              )}

              {settingsItems.length > 0 && (
                <Command.Group heading="Settings" className="mb-2">
                  {settingsItems.map((item) => (
                    <Command.Item
                      key={item.id}
                      onSelect={() => handleSelect(item)}
                      className="flex cursor-pointer items-center rounded-md px-4 py-2 text-sm hover:bg-gray-100 aria-selected:bg-gray-100"
                    >
                      <span className="mr-3 text-gray-500">{item.icon}</span>
                      <span>{item.label}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              )}
            </>
          )}
        </Command.List>

        <div className="flex items-center justify-between border-t px-4 py-2 text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span>
              <kbd className="rounded border px-1.5 py-0.5 font-mono text-xs">↑↓</kbd> to navigate
            </span>
            <span>
              <kbd className="rounded border px-1.5 py-0.5 font-mono text-xs">Enter</kbd> to select
            </span>
          </div>
          <span>
            <kbd className="rounded border px-1.5 py-0.5 font-mono text-xs">Esc</kbd> to close
          </span>
        </div>
      </div>
    </Command.Dialog>
  );
};

export default CommandPalette;
