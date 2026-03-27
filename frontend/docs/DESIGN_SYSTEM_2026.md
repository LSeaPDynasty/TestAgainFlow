# TestFlow 2026 设计优化方案

> 版本: v2.0
> 更新时间: 2026-03-27
> 设计师: Claude Design Team

---

## 📋 目录

- [设计理念](#设计理念)
- [一、设计系统重构](#一设计系统重构)
- [二、布局架构优化](#二布局架构优化)
- [三、核心页面优化](#三核心页面优化)
- [四、组件库优化](#四组件库优化)
- [五、交互优化](#五交互优化)
- [六、性能优化](#六性能优化)
- [七、可访问性](#七可访问性)
- [八、实施路线图](#八实施路线图)
- [九、技术选型](#九技术选型)

---

## 🎨 设计理念

**"测试的优雅，在于简单与强大的平衡"**

### 核心原则

1. **专业工具感** - 而非通用SaaS，体现测试工程师的专业性
2. **信息密度优先** - 在有限空间展示更多有价值信息
3. **操作效率至上** - 减少点击次数，提升流畅度
4. **渐进式复杂** - 新手友好，专家高效

---

## 一、设计系统重构

### 1.1 色彩系统

#### 品牌色 - 科技蓝

```typescript
// src/styles/theme.ts
export const theme = {
  primary: {
    50:  '#E6F4FF',
    100: '#BAE0FF',
    200: '#91CAFF',
    300: '#69B1FF',
    400: '#4096FF',  // 主色
    500: '#1677FF',
    600: '#0958D9',
    700: '#003EB3',
    800: '#002C8C',
    900: '#001D66',
  }
}
```

#### 语义色

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| Success | `#52C41A` | 测试通过、操作成功 |
| Warning | `#FAAD14` | 警告提示 |
| Error | `#FF4D4F` | 测试失败、错误 |
| Info | `#1677FF` | 信息提示 |

#### 测试专用色

```typescript
test: {
  p0: '#FF4D4F',      // P0 - 红色（最高优先级）
  p1: '#FAAD14',      // P1 - 橙色
  p2: '#FADB14',      // P2 - 黄色
  p3: '#8C8C8C',      // P3 - 灰色（最低优先级）
  running: '#1677FF', // 运行中
  pending: '#8C8C8C', // 等待
}
```

#### 中性色

```typescript
gray: {
  50:  '#FAFAFA',  // 背景基础
  100: '#F5F5F5',  // 次级背景
  200: '#E8E8E8',  // 边框
  300: '#D9D9D9',  // 分割线
  400: '#BFBFBF',  // 禁用文本
  500: '#8C8C8C',  // 次级文本
  600: '#595959',  // 常规文本
  700: '#434343',  // 标题文本
  800: '#262626',  // 强调文本
  900: '#1F1F1F',  // 最强文本
}
```

### 1.2 字体系统

```typescript
export const typography = {
  // 字体家族
  fontFamily: {
    sans: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`,
    mono: `'JetBrains Mono', 'Fira Code', 'Consolas', monospace`,
  },

  // 字号 - 采用 8px 基准
  fontSize: {
    xs: '0.75rem',    // 12px - 辅助文本
    sm: '0.875rem',   // 14px - 正文
    base: '1rem',     // 16px - 默认
    lg: '1.125rem',   // 18px - 小标题
    xl: '1.25rem',    // 20px - 标题
    '2xl': '1.5rem',  // 24px - 大标题
    '3xl': '1.875rem',// 30px - 页面标题
    '4xl': '2.25rem', // 36px - 特大标题
  },

  // 字重
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // 行高
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  }
}
```

### 1.3 间距系统（8px基准）

```typescript
export const spacing = {
  0: '0',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
}
```

### 1.4 圆角系统

```typescript
export const borderRadius = {
  none: '0',
  sm: '0.25rem',   // 4px - 小元素（Tag、Badge）
  base: '0.5rem',  // 8px - 卡片、按钮
  lg: '0.75rem',   // 12px - 大卡片
  xl: '1rem',      // 16px - 模态框
  full: '9999px',  // 圆形（头像）
}
```

### 1.5 阴影系统

```typescript
export const shadow = {
  xs: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  sm: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  base: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  md: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  lg: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  xl: '0 25px 50px -12px rgb(0 0 0 / 0.25)',
}
```

---

## 二、布局架构优化

### 2.1 整体布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  Header (56px)                                                   │
│  ┌──────┐ ┌─────────────┐ ┌────────────────┐ ┌──────────────┐  │
│  │ Logo │ │ 全局搜索     │ │ 项目切换器     │ │ 用户菜单     │  │
│  └──────┘ └─────────────┘ └────────────────┘ └──────────────┘  │
├───┬─────────────────────────────────────────────────────────────┤
│ S │                                                             │
│ i │                                                             │
│ d │     主内容区                                                  │
│ e │     (动态padding，支持日志面板展开)                            │
│ b │                                                             │
│ a │                                                             │
│ r │                                                             │
│   │                                                             │
│(  │                                                             │
│ 2 │                                                             │
│ 0 │                                                             │
│ 0 │                                                             │
│ p │                                                             │
│ x │                                                             │
│ ) │                                                             │
├───┴─────────────────────────────────────────────────────────────┤
│  Command Bar (48px) - 可选显示                                    │
│  快速操作、执行控制台入口                                          │
└─────────────────────────────────────────────────────────────────┘
│  Log Panel (可展开 0-360px)                                       │
│  执行日志、实时状态                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 侧边栏优化

#### 特性
- **可折叠**：展开 200px / 折叠 60px
- **分组导航**：折叠分组，减少视觉压力
- **数量徽标**：实时显示项目数量
- **激活指示**：左侧蓝色竖线
- **快捷键**：支持数字键快速切换

#### 导航分组

| 分组 | 导航项 |
|------|--------|
| **资源管理** | 界面、元素、步骤、流程、用例、套件 |
| **执行中心** | 执行、历史、定时任务 |
| **配置** | 设备、环境、项目、标签 |

#### 实现代码

```tsx
// src/components/Sidebar/index.tsx

const sections = {
  manage: {
    label: '资源管理',
    items: [
      { key: 'screens', icon: <MobileOutlined />, label: '界面', badge: count.screens },
      { key: 'elements', icon: <AppstoreOutlined />, label: '元素', badge: count.elements },
      { key: 'steps', icon: <BlockOutlined />, label: '步骤', badge: count.steps },
      { key: 'flows', icon: <BranchesOutlined />, label: '流程', badge: count.flows },
      { key: 'testcases', icon: <FileTextOutlined />, label: '用例', badge: count.testcases },
      { key: 'suites', icon: <FolderOutlined />, label: '套件', badge: count.suites },
    ]
  },
  execute: {
    label: '执行中心',
    items: [
      { key: 'runs', icon: <PlayCircleOutlined />, label: '执行', badge: count.running },
      { key: 'history', icon: <HistoryOutlined />, label: '历史' },
      { key: 'schedules', icon: <CalendarOutlined />, label: '定时任务' },
    ]
  },
  config: {
    label: '配置',
    items: [
      { key: 'devices', icon: <LaptopOutlined />, label: '设备', badge: `${onlineDevices}/${totalDevices}` },
      { key: 'profiles', icon: <DatabaseOutlined />, label: '环境' },
      { key: 'projects', icon: <ProjectOutlined />, label: '项目' },
    ]
  }
}
```

### 2.3 Header 优化

#### 新增功能

1. **全局搜索** - 支持 `Cmd+K` 快捷键
2. **通知中心** - 显示执行完成、失败提醒
3. **设备状态** - 实时显示在线设备数量
4. **Logo 动画** - 呼吸效果

#### 布局

```
┌─────────────────────────────────────────────────────────────┐
│ [☰] ● TestFlow    [🔍 搜索...]  [项目▼]  [设备 3/5]  [🔔]  [👤] │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、核心页面优化

### 3.1 Dashboard 重设计

#### 布局

```
┌─────────────────────────────────────────────────────────────┐
│  控制板                                                      │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│ │ 总用例  │ │ 通过率  │ │ 在线设备 │ │ 今日执行 │            │
│ │   128   │ │  85.3%  │ │  3/5    │ │   42    │            │
│ │  +12%   │ │  +5%    │ │         │ │  +23%   │            │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
├────────────────────────────────────┬─────────────────────────┤
│  执行趋势（折线图）                  │  快速操作               │
│  ┌─────────────────────────────┐   │  ┌───────────────────┐ │
│  │                             │   │  │ 新建用例          │ │
│  │    ╱╲    ╱─╲               │   │  │ 执行测试          │ │
│  │   ╱  ╲  ╱   ╲   ╱╲         │   │  │ 管理设备          │ │
│  │  ╱    ╲╱     ╲ ╱  ╲        │   │  │ 查看报告          │ │
│  │                             │   │  └───────────────────┘ │
│  └─────────────────────────────┘   │  最近执行               │
│  失败 Top 10（柱状图）              │  ┌───────────────────┐ │
│  ┌─────────────────────────────┐   │  │ ✓ 登录测试        │ │
│  │                             │   │  │ ✗ 支付流程        │ │
│  │  ██                         │   │  │ ✓ 注册流程        │ │
│  │  ████                       │   │  └───────────────────┘ │
│  └─────────────────────────────┘   └─────────────────────────┘
└────────────────────────────────────┴─────────────────────────┘
```

#### StatCard 组件

```tsx
interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;  // "+12%" / "-5%"
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'red';
  chart?: React.ReactNode;  // 迷你图表
  loading?: boolean;
}
```

### 3.2 元素管理优化

#### 新增特性

| 特性 | 说明 |
|------|------|
| 批量操作 | 支持批量编辑、删除、测试 |
| 视图切换 | 列表视图 vs 卡片视图 |
| 虚拟滚动 | 支持大数据量（10000+） |
| 紧凑模式 | 增加信息密度 |
| 快捷键 | Ctrl+N 新建、Delete 删除 |

#### 工具栏

```
┌─────────────────────────────────────────────────────────────┐
│ [🔍 搜索...] [筛选▼] [视图切换]  [批量操作(3)]  [+ 新建元素] │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 流程编辑器优化

#### 新布局：三栏式

```
┌─────────────────────────────────────────────────────────────┐
│  流程编辑器                                                   │
├──────────┬──────────────────────────────┬───────────────────┤
│          │                              │                   │
│ 步骤库   │         画布区               │   属性面板        │
│          │                              │                   │
│ [搜索]   │  ┌──────────────────────┐   │  步骤名称:        │
│          │  │  ① 点击登录按钮      │   │  [点击登录]       │
│ ▼ 界面   │  │  ② 输入用户名        │   │                   │
│   ├ 登录 │  │  ③ 输入密码          │   │  操作类型:        │
│   ├ 注册 │  │  ④ 点击登录          │   │  [click ▼]       │
│          │  │                      │   │                   │
│ ▼ 步骤   │  │  [拖拽步骤到此处]     │   │  目标元素:        │
│   ├ 点击 │  │                      │   │  [登录按钮 ▼]     │
│   ├ 输入 │  └──────────────────────┘   │                   │
│   ├ 断言 │                              │  [保存] [取消]     │
│          │                              │                   │
└──────────┴──────────────────────────────┴───────────────────┘
```

#### 特性

- **拖拽编排**：从步骤库拖拽到画布
- **实时预览**：步骤效果实时预览
- **属性编辑**：右侧面板编辑选中步骤
- **快捷键**：
  - `Ctrl+S` - 保存
  - `Ctrl+Z` - 撤销
  - `Delete` - 删除选中
  - `Ctrl+D` - 复制

---

## 四、组件库优化

### 4.1 StatCard 组件

```tsx
// src/components/StatCard/index.tsx

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'red';
  chart?: React.ReactNode;
  loading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  trend,
  icon,
  color = 'blue',
  chart,
  loading,
}) => {
  return (
    <div className={cn('stat-card', `stat-card-${color}`)}>
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        {trend && (
          <span className={cn(
            'stat-card-trend',
            trend.startsWith('+') ? 'positive' : 'negative'
          )}>
            {trend}
          </span>
        )}
      </div>

      <div className="stat-card-body">
        <div className="stat-card-value">{value}</div>
        {icon && (
          <div className="stat-card-icon">
            {icon}
          </div>
        )}
      </div>

      {chart && (
        <div className="stat-card-chart">
          {chart}
        </div>
      )}
    </div>
  );
};
```

### 4.2 GlobalSearch 组件

```tsx
// src/components/GlobalSearch/index.tsx

export const GlobalSearch: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');

  const { data: results } = useQuery({
    queryKey: ['global-search', search],
    queryFn: () => globalSearch(search),
    enabled: search.length >= 2,
  });

  useHotkeys('cmd+k', (e) => {
    e.preventDefault();
    setOpen(true);
  });

  return (
    <>
      <Input
        placeholder="搜索元素、步骤、流程、用例... (⌘K)"
        onFocus={() => setOpen(true)}
        prefix={<SearchOutlined />}
        style={{ width: 400 }}
      />

      <Modal
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        width={640}
        closable={false}
      >
        <Input
          size="large"
          placeholder="输入关键词搜索..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
          prefix={<SearchOutlined />}
          suffix={<span className="hotkey-hint">ESC</span>}
        />

        <div className="search-results">
          {/* 搜索结果分组展示 */}
        </div>
      </Modal>
    </>
  );
};
```

### 4.3 LogPanel 优化

```tsx
// src/components/LogPanel/index.tsx

export const LogPanel: React.FC = () => {
  const { logs, height } = useLogs();
  const [filter, setFilter] = useState<LogLevel>('all');
  const [autoScroll, setAutoScroll] = useState(true);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  return (
    <div
      className="log-panel"
      style={{ height: `${height}px` }}
    >
      <div className="log-panel-header">
        <Space>
          <Badge count={logs.filter(l => l.level === 'error').length}>
            <Button icon={<BugOutlined />}>错误</Button>
          </Badge>
          <LogLevelFilter value={filter} onChange={setFilter} />
        </Space>
        <Space>
          <Switch
            checked={autoScroll}
            onChange={setAutoScroll}
            checkedChildren="自动滚动"
            unCheckedChildren="手动"
          />
          <Button icon={<DownloadOutlined />}>导出</Button>
          <Button icon={<CloseOutlined />} onClick={close} />
        </Space>
      </div>

      <div className="log-panel-body">
        <VirtualizedList
          height={height - 48}
          itemCount={logs.length}
          itemSize={32}
          renderItem={({ index, style }) => (
            <LogEntry
              key={index}
              log={logs[index]}
              style={style}
            />
          )}
        />
        <div ref={bottomRef} />
      </div>

      <ResizeHandle
        onResize={(newHeight) => setHeight(newHeight)}
      />
    </div>
  );
};
```

---

## 五、交互优化

### 5.1 快捷键系统

#### 全局快捷键

| 快捷键 | 功能 |
|--------|------|
| `Cmd+K` | 打开全局搜索 |
| `Cmd+Shift+C` | 打开命令面板 |
| `Cmd+N` | 新建（当前页面） |
| `Cmd+S` | 保存 |
| `Escape` | 关闭弹窗/抽屉 |
| `/` | 聚焦搜索框 |

#### 列表页快捷键

| 快捷键 | 功能 |
|--------|------|
| `↑` / `↓` | 上下移动选中 |
| `Enter` | 打开/编辑选中项 |
| `Space` | 预览选中项 |
| `Delete` | 删除选中项 |
| `Ctrl+D` | 复制选中项 |

#### 实现代码

```typescript
// src/hooks/useHotkeys.ts

export const useHotkeys = (key: string, callback: () => void) => {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      if (modKey && e.key === key.toLowerCase()) {
        e.preventDefault();
        callback();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [key, callback]);
};
```

### 5.2 命令面板

```tsx
// src/components/CommandPalette/index.tsx

export const CommandPalette: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');

  const commands = [
    {
      id: 'create-element',
      label: '新建元素',
      icon: <PlusOutlined />,
      action: () => navigate('/elements?action=create'),
      shortcut: 'N',
    },
    {
      id: 'create-flow',
      label: '新建流程',
      icon: <PlusOutlined />,
      action: () => navigate('/flows?action=create'),
      shortcut: 'F',
    },
    // ...更多命令
  ];

  useHotkeys('cmd+shift+c', () => setOpen(true));

  return (
    <Modal
      open={open}
      onCancel={() => setOpen(false)}
      footer={null}
      width={640}
      closable={false}
    >
      <Input
        size="large"
        placeholder="输入命令或搜索..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        autoFocus
        prefix={<CommandOutlined />}
      />

      <CommandList
        commands={commands.filter(c =>
          c.label.toLowerCase().includes(search.toLowerCase())
        )}
        onSelect={(command) => {
          command.action();
          setOpen(false);
        }}
      />
    </Modal>
  );
};
```

### 5.3 乐观更新

```typescript
// src/hooks/useOptimisticMutation.ts

export const useOptimisticMutation = <T,>(
  mutationFn: (data: T) => Promise<void>,
  queryKey: string[]
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: T) => {
      // 乐观更新
      queryClient.setQueryData(queryKey, (old: any) => [
        ...old,
        { ...data, id: `temp-${Date.now()}`, isPending: true },
      ]);

      try {
        await mutationFn(data);
      } catch (error) {
        // 失败回滚
        queryClient.invalidateQueries({ queryKey });
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });
};
```

---

## 六、性能优化

### 6.1 虚拟滚动

```tsx
// src/components/VirtualizedList/index.tsx

import { useVirtualizer } from '@tanstack/react-virtual';

export const VirtualizedList: React.FC<VirtualizedListProps> = ({
  items,
  height,
  itemSize,
  renderItem,
}) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemSize,
    overscan: 5,
  });

  return (
    <div
      ref={parentRef}
      style={{ height, overflow: 'auto' }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${itemSize}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem({ index: virtualItem.index, data: items[virtualItem.index] })}
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 6.2 代码分割

```tsx
// src/App.tsx

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Elements = lazy(() => import('./pages/Elements'));
// ...其他页面

// 预加载关键路由
const preloadRoute = (path: string) => {
  switch (path) {
    case '/elements':
      import('./pages/Elements');
      break;
    case '/flows':
      import('./pages/Flows');
      break;
  }
};

// 在Sidebar hover时预加载
<Sidebar
  onItemHover={(key) => preloadRoute(key)}
/>
```

### 6.3 防抖与节流

```typescript
// src/utils/performance.ts

export const useDebounce = <T,>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

export const useThrottle = <T,>(value: T, limit: number): T => {
  const [throttledValue, setThrottledValue] = useState(value);
  const lastRan = useRef(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        setThrottledValue(value);
        lastRan.current = Date.now();
      }
    }, limit - (Date.now() - lastRan.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, limit]);

  return throttledValue;
};
```

---

## 七、可访问性

### 7.1 ARIA支持

```tsx
// 按钮
<Button
  aria-label="新建元素"
  icon={<PlusOutlined />}
  onClick={handleCreate}
>
  <span className="sr-only">新建元素</span>
</Button>

// 表格
<Table
  aria-label="元素列表"
  caption="当前项目的所有UI元素"
  columns={columns}
  dataSource={elements}
/>

// 模态框
<Modal
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <h2 id="modal-title">新建元素</h2>
  <p id="modal-description">请填写元素信息</p>
</Modal>
```

### 7.2 键盘导航

```typescript
// 键盘导航Hook
export const useKeyboardNavigation = (items: any[]) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          setSelectedIndex((i) => Math.min(i + 1, items.length - 1));
          break;
        case 'ArrowUp':
          setSelectedIndex((i) => Math.max(i - 1, 0));
          break;
        case 'Enter':
          items[selectedIndex]?.action?.();
          break;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [items, selectedIndex]);

  return { selectedIndex, setSelectedIndex };
};
```

### 7.3 屏幕阅读器优化

```css
/* sr-only 类 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* 焦点可见 */
:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}
```

---

## 八、实施路线图

### Phase 1: 基础设施（2周）

- [ ] 设计系统搭建
  - [ ] 色彩系统
  - [ ] 字体系统
  - [ ] 间距/圆角/阴影系统
- [ ] 主题系统实现
- [ ] 基础组件库
  - [ ] Button
  - [ ] Input
  - [ ] Card
  - [ ] Modal
  - [ ] StatCard
- [ ] 布局架构重构
  - [ ] Header
  - [ ] Sidebar
  - [ ] Layout

### Phase 2: 核心页面（3周）

- [ ] Dashboard重设计
  - [ ] 统计卡片
  - [ ] 图表组件
  - [ ] 快速操作
- [ ] 元素管理优化
  - [ ] 批量操作
  - [ ] 视图切换
  - [ ] 虚拟滚动
- [ ] 流程编辑器优化
  - [ ] 可视化编排
  - [ ] 拖拽功能
  - [ ] 属性面板
- [ ] 用例管理优化
  - [ ] Items编辑器
  - [ ] 批量导入

### Phase 3: 交互增强（2周）

- [ ] 快捷键系统
- [ ] 命令面板
- [ ] 全局搜索
- [ ] 乐观更新
- [ ] Toast通知优化

### Phase 4: 性能与无障碍（1周）

- [ ] 虚拟滚动
- [ ] 代码分割
- [ ] ARIA支持
- [ ] 键盘导航
- [ ] 屏幕阅读器优化

---

## 九、技术选型

### 依赖包

```json
{
  "dependencies": {
    "@tanstack/react-virtual": "^3.10.0",
    "recharts": "^2.12.0",
    "react-hotkeys-hook": "^4.5.0",
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "cmdk": "^1.0.0",
    "sonner": "^1.5.0",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "@tailwindcss/forms": "^0.5.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0",
    "@types/node": "^20.0.0"
  }
}
```

### 目录结构

```
src/
├── components/
│   ├── StatCard/
│   ├── GlobalSearch/
│   ├── CommandPalette/
│   ├── LogPanel/
│   ├── VirtualizedList/
│   └── Sidebar/
├── pages/
│   ├── Dashboard/
│   ├── Elements/
│   ├── Flows/
│   └── Testcases/
├── hooks/
│   ├── useHotkeys.ts
│   ├── useOptimisticMutation.ts
│   ├── useDebounce.ts
│   └── useVirtualizer.ts
├── styles/
│   ├── theme.ts
│   └── globals.css
└── utils/
    ├── cn.ts
    └── performance.ts
```

---

## 十、设计资源

### Figma 设计系统

建议创建 Figma 设计系统，包含：
- 色彩规范
- 字体规范
- 组件库（Button、Input、Card等）
- 图标库（使用 Ant Design Icons）
- 页面模板

### 图标选择

继续使用 Ant Design Icons，统一使用 Outline 风格。

### 设计参考

- [Linear](https://linear.app) - 设计系统参考
- [Vercel](https://vercel.com) - 极简风格参考
- [GitHub](https://github.com) - 专业工具参考

---

**文档版本**: v2.0
**最后更新**: 2026-03-27
**维护者**: Design Team