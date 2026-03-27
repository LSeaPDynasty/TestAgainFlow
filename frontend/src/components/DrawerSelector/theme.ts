/**
 * DrawerSelector 主题配置
 * 提供多种预设主题，统一所有抽屉选择器的视觉风格
 */

export interface DrawerSelectorTheme {
  name: string;
  className: string;
  styles: {
    triggerBg: string;
    triggerBorder: string;
    triggerBorderHover: string;
    triggerRadius: number;
    triggerHeight: number;
    drawerWidth: number;
    drawerBg: string;
    drawerBorder: string;
    drawerShadow: string;
    drawerRadius: number;
    headerBg: string;
    headerBorder: string;
    headerText: string;
    itemPadding: string;
    itemBorder: string;
    itemHoverBg: string;
    itemSelectedBg: string;
    itemSelectedBorder: string;
    itemRadius: number;
    itemHeight: number;
    textPrimary: string;
    textSecondary: string;
    textSelected: string;
  };
}

// ========== 预设主题 ==========

export const DRAWER_SELECTOR_THEMES: Record<string, DrawerSelectorTheme> = {
  default: {
    name: '默认主题',
    className: 'drawer-selector-default',
    styles: {
      triggerBg: '#ffffff',
      triggerBorder: '#d9d9d9',
      triggerBorderHover: '#4096ff',
      triggerRadius: 6,
      triggerHeight: 32,
      drawerWidth: 480,
      drawerBg: '#ffffff',
      drawerBorder: '#f0f0f0',
      drawerShadow: '0 6px 16px rgba(0, 0, 0, 0.08)',
      drawerRadius: 8,
      headerBg: '#fafafa',
      headerBorder: '#f0f0f0',
      headerText: '#262626',
      itemPadding: '12px 16px',
      itemBorder: '#f0f0f0',
      itemHoverBg: '#f5f5f5',
      itemSelectedBg: '#e6f7ff',
      itemSelectedBorder: '#1890ff',
      itemRadius: 4,
      itemHeight: 64,
      textPrimary: 'rgba(0, 0, 0, 0.85)',
      textSecondary: 'rgba(0, 0, 0, 0.45)',
      textSelected: '#1890ff',
    },
  },

  modern: {
    name: '现代主题',
    className: 'drawer-selector-modern',
    styles: {
      triggerBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      triggerBorder: 'none',
      triggerBorderHover: 'none',
      triggerRadius: 8,
      triggerHeight: 36,
      drawerWidth: 520,
      drawerBg: '#ffffff',
      drawerBorder: 'none',
      drawerShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
      drawerRadius: 12,
      headerBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      headerBorder: 'none',
      headerText: '#ffffff',
      itemPadding: '16px 20px',
      itemBorder: '#f0f0f0',
      itemHoverBg: 'linear-gradient(90deg, #f8f9ff 0%, #ffffff 100%)',
      itemSelectedBg: 'linear-gradient(90deg, #e8ecff 0%, #f8f9ff 100%)',
      itemSelectedBorder: '#667eea',
      itemRadius: 8,
      itemHeight: 72,
      textPrimary: '#1a1a2e',
      textSecondary: '#4a5568',
      textSelected: '#667eea',
    },
  },

  dark: {
    name: '深色主题',
    className: 'drawer-selector-dark',
    styles: {
      triggerBg: '#1f2937',
      triggerBorder: '#374151',
      triggerBorderHover: '#60a5fa',
      triggerRadius: 6,
      triggerHeight: 32,
      drawerWidth: 480,
      drawerBg: '#111827',
      drawerBorder: '#374151',
      drawerShadow: '0 6px 16px rgba(0, 0, 0, 0.4)',
      drawerRadius: 8,
      headerBg: '#1f2937',
      headerBorder: '#374151',
      headerText: '#f3f4f6',
      itemPadding: '12px 16px',
      itemBorder: '#374151',
      itemHoverBg: '#374151',
      itemSelectedBg: '#1e3a8a20',
      itemSelectedBorder: '#60a5fa',
      itemRadius: 4,
      itemHeight: 64,
      textPrimary: '#f3f4f6',
      textSecondary: '#9ca3af',
      textSelected: '#60a5fa',
    },
  },

  compact: {
    name: '紧凑主题',
    className: 'drawer-selector-compact',
    styles: {
      triggerBg: '#ffffff',
      triggerBorder: '#d9d9d9',
      triggerBorderHover: '#4096ff',
      triggerRadius: 4,
      triggerHeight: 28,
      drawerWidth: 400,
      drawerBg: '#ffffff',
      drawerBorder: '#f0f0f0',
      drawerShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      drawerRadius: 4,
      headerBg: '#fafafa',
      headerBorder: '#f0f0f0',
      headerText: '#262626',
      itemPadding: '8px 12px',
      itemBorder: '#f0f0f0',
      itemHoverBg: '#fafafa',
      itemSelectedBg: '#e6f7ff',
      itemSelectedBorder: '#1890ff',
      itemRadius: 2,
      itemHeight: 48,
      textPrimary: 'rgba(0, 0, 0, 0.85)',
      textSecondary: 'rgba(0, 0, 0, 0.45)',
      textSelected: '#1890ff',
    },
  },
};

// ========== 默认主题导出 ==========

export const DEFAULT_THEME = 'default';

// ========== 工具函数 ==========

/**
 * 获取主题样式
 */
export function getThemeStyles(themeName: string = DEFAULT_THEME) {
  return DRAWER_SELECTOR_THEMES[themeName]?.styles || DRAWER_SELECTOR_THEMES.default.styles;
}

/**
 * 获取主题类名
 */
export function getThemeClassName(themeName: string = DEFAULT_THEME) {
  return DRAWER_SELECTOR_THEMES[themeName]?.className || DRAWER_SELECTOR_THEMES.default.className;
}

/**
 * 应用主题到抽屉
 */
export function applyThemeToDrawer(drawerElement: HTMLElement, themeName: string = DEFAULT_THEME) {
  const theme = DRAWER_SELECTOR_THEMES[themeName];
  if (!theme || !drawerElement) return;

  // 应用主题类名
  drawerElement.className = theme.className;

  // 应用自定义样式
  const styles = theme.styles;
  drawerElement.style.setProperty('--drawer-width', `${styles.drawerWidth}px`);
  // ... 可以应用更多样式变量
}

/**
 * 获取所有可用主题列表
 */
export function getAvailableThemes() {
  return Object.entries(DRAWER_SELECTOR_THEMES).map(([key, theme]) => ({
    value: key,
    label: theme.name,
    className: theme.className,
  }));
}
