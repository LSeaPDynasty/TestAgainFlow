/**
 * DrawerSelector 全局配置
 * 统一管理所有抽屉选择器的默认配置
 */

import { DRAWER_SELECTOR_THEMES, getThemeClassName } from './theme';

// ========== 全局默认配置 ==========

export const DRAWER_SELECTOR_DEFAULT_CONFIG = {
  // 默认主题
  theme: 'default' as keyof typeof DRAWER_SELECTOR_THEMES,

  // UI默认配置
  drawerWidth: 480,
  placement: 'right' as 'left' | 'right',
  searchable: true,
  allowClear: true,
  showCount: true,

  // 动画配置
  animationDuration: 300,
  animationEasing: 'cubic-bezier(0.4, 0, 0.2, 1)',

  // 滚动配置
  virtualScroll: false,
  virtualScrollItemHeight: 64,

  // 搜索配置
  searchDelay: 300, // 防抖延迟（毫秒）
  searchMinLength: 0,

  // 分页配置
  pageSize: 20,
  pageSizeOptions: [10, 20, 50, 100],

  // 性能配置
  lazyLoad: true,
  cacheOptions: true,
  cacheExpire: 5 * 60 * 1000, // 5分钟
};

// ========== 页面级配置 ==========

/**
 * Steps页面配置
 */
export const STEPS_PAGE_SELECTOR_CONFIG = {
  ...DRAWER_SELECTOR_DEFAULT_CONFIG,

  // Screen选择器
  screen: {
    drawerWidth: 400,
    placement: 'right' as const,
    searchable: true,
    showCount: false,
    renderExtra: (option: any) => (
      <span style={{ fontSize: 12, color: '#999' }}>
        {option.element_count} 个元素
      </span>
    ),
  },

  // Action Type选择器
  actionType: {
    drawerWidth: 360,
    placement: 'right' as const,
    searchable: true,
    showCount: false,
    groupBy: 'category', // 按分类分组
  },

  // Element选择器
  element: {
    drawerWidth: 420,
    placement: 'right' as const,
    searchable: true,
    showCount: false,
    renderExtra: (option: any) => (
      <span style={{ fontSize: 11, color: '#999' }}>
        {option.locators?.[0]?.type}
      </span>
    ),
  },
};

/**
 * Flows页面配置
 */
export const FLOWS_PAGE_SELECTOR_CONFIG = {
  ...DRAWER_SELECTOR_DEFAULT_CONFIG,

  // Step选择器
  step: {
    drawerWidth: 420,
    placement: 'right' as const,
    searchable: true,
    showCount: false,
    renderExtra: (option: any) => (
      <span style={{ fontSize: 12, color: '#999' }}>
        {option.action_type}
      </span>
    ),
  },

  // subFlow选择器
  subFlow: {
    drawerWidth: 400,
    placement: 'right' as const,
    searchable: true,
  },
};

/**
 * Testcases页面配置
 */
export const TESTCASES_PAGE_SELECTOR_CONFIG = {
  ...DRAWER_SELECTOR_DEFAULT_CONFIG,

  // Flow选择器
  flow: {
    drawerWidth: 440,
    placement: 'right' as const,
    searchable: true,
    showCount: false,
    renderExtra: (option: any) => (
      <span style={{ fontSize: 12, color: '#999' }}>
        {option.step_count} 个步骤
      </span>
    ),
  },

  // Tag选择器（多选）
  tag: {
    drawerWidth: 320,
    placement: 'right' as const,
    searchable: true,
    multiple: true,
  },
};

/**
 * Elements页面配置
 */
export const ELEMENTS_PAGE_SELECTOR_CONFIG = {
  ...DRAWER_SELECTOR_DEFAULT_CONFIG,

  // Screen选择器
  screen: {
    drawerWidth: 400,
    placement: 'right' as const,
    searchable: true,
    showCount: false,
  },
};

/**
 * Suites页面配置
 */
export const SUITES_PAGE_SELECTOR_CONFIG = {
  ...DRAWER_SELECTOR_DEFAULT_CONFIG,

  // Testcase选择器（多选）
  testcase: {
    drawerWidth: 500,
    placement: 'right' as const,
    searchable: true,
    multiple: true,
    pageSize: 50,
  },
};

// ========== 工具函数 ==========

/**
 * 获取页面级配置
 */
export function getPageSelectorConfig(pageName: string, selectorName?: string) {
  const pageConfigs: Record<string, any> = {
    steps: STEPS_PAGE_SELECTOR_CONFIG,
    flows: FLOWS_PAGE_SELECTOR_CONFIG,
    testcases: TESTCASES_PAGE_SELECTOR_CONFIG,
    elements: ELEMENTS_PAGE_SELECTOR_CONFIG,
    suites: SUITES_PAGE_SELECTOR_CONFIG,
  };

  const pageConfig = pageConfigs[pageName];
  if (!pageConfig) return DRAWER_SELECTOR_DEFAULT_CONFIG;

  if (selectorName && pageConfig[selectorName]) {
    return pageConfig[selectorName];
  }

  return pageConfig;
}

/**
 * 合并配置
 */
export function mergeConfig(defaultConfig: any, userConfig: any) {
  return {
    ...defaultConfig,
    ...userConfig,
    styles: {
      ...defaultConfig.styles,
      ...userConfig.styles,
    },
  };
}

/**
 * 应用主题到配置
 */
export function applyTheme(config: any, themeName?: string) {
  const finalTheme = themeName || config.theme || DRAWER_SELECTOR_DEFAULT_CONFIG.theme;
  return {
    ...config,
    theme: finalTheme,
    className: getThemeClassName(finalTheme),
  };
}
