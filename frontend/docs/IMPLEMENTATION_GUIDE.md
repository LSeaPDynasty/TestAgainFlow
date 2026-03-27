# TestFlow 设计系统实施指南

> 本文档指导开发团队如何逐步实施新的设计系统

---

## 📅 实施计划

### 总体时间线

```
Week 1-2:  基础设施搭建
Week 3-5:  核心页面重构
Week 6-7:  交互增强
Week 8:    性能与无障碍优化
Week 9:    测试与调优
Week 10:   上线与文档
```

---

## Phase 1: 基础设施搭建 (Week 1-2)

### 1.1 安装依赖

```bash
cd testflow/frontend
npm install @tanstack/react-virtual recharts react-hotkeys-hook
npm install @dnd-kit/core @dnd-kit/sortable cmdk sonner
npm install -D tailwindcss @tailwindcss/forms
npm install -D clsx tailwind-merge
```

### 1.2 配置 Tailwind CSS

```bash
npx tailwindcss init -p
```

**tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E6F4FF',
          100: '#BAE0FF',
          200: '#91CAFF',
          300: '#69B1FF',
          400: '#4096FF',
          500: '#1677FF',
          600: '#0958D9',
          700: '#003EB3',
          800: '#002C8C',
          900: '#001D66',
        },
        success: '#52C41A',
        warning: '#FAAD14',
        error: '#FF4D4F',
        info: '#1677FF',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
```

**src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* 自定义样式 */
@layer base {
  :root {
    color-scheme: light;
  }

  body {
    @apply bg-gray-50 text-gray-900;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
  }

  .btn-primary {
    @apply bg-primary-500 text-white hover:bg-primary-600;
  }

  .card {
    @apply bg-white rounded-lg shadow-sm border border-gray-200;
  }
}
```

### 1.3 创建工具函数

**src/utils/cn.ts**

```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 1.4 创建主题配置

**src/styles/theme.ts**

```typescript
export const theme = {
  colors: {
    primary: {
      50: '#E6F4FF',
      100: '#BAE0FF',
      200: '#91CAFF',
      300: '#69B1FF',
      400: '#4096FF',
      500: '#1677FF',
      600: '#0958D9',
      700: '#003EB3',
      800: '#002C8C',
      900: '#001D66',
    },
    success: '#52C41A',
    warning: '#FAAD14',
    error: '#FF4D4F',
    info: '#1677FF',
  },
  spacing: {
    1: '0.25rem',  // 4px
    2: '0.5rem',   // 8px
    3: '0.75rem',  // 12px
    4: '1rem',     // 16px
    5: '1.25rem',  // 20px
    6: '1.5rem',   // 24px
    8: '2rem',     // 32px
  },
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    base: '1rem',    // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.875rem', // 30px
  },
};
```

### 1.5 创建基础组件

**src/components/ui/Button.tsx**

```tsx
import { cn } from '@/utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'button',
        `button-${variant}`,
        `button-${size}`,
        (disabled || loading) && 'button-disabled',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="button-spinner" />}
      {children}
    </button>
  );
}
```

**src/components/ui/Card.tsx**

```tsx
import { cn } from '@/utils/cn';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  extra?: React.ReactNode;
}

export function Card({ children, className, title, extra }: CardProps) {
  return (
    <div className={cn('card', className)}>
      {(title || extra) && (
        <div className="card-header">
          {title && <h3 className="card-title">{title}</h3>}
          {extra && <div className="card-extra">{extra}</div>}
        </div>
      )}
      <div className="card-body">
        {children}
      </div>
    </div>
  );
}
```

---

## Phase 2: 核心页面重构 (Week 3-5)

### 2.1 Dashboard 重构

**创建 StatCard 组件**

```tsx
// src/components/StatCard.tsx
import { cn } from '@/utils/cn';

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'purple';
}

export function StatCard({
  title,
  value,
  trend,
  icon,
  color = 'blue',
}: StatCardProps) {
  const colorMap = {
    blue: 'bg-primary-500',
    green: 'bg-success',
    orange: 'bg-warning',
    purple: 'bg-purple-500',
  };

  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        {trend && (
          <span className={cn(
            'stat-card-trend',
            trend.startsWith('+') ? 'text-success' : 'text-error'
          )}>
            {trend}
          </span>
        )}
      </div>

      <div className="stat-card-body">
        <div className="stat-card-value">{value}</div>
        {icon && (
          <div className={cn('stat-card-icon', colorMap[color])}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
```

**更新 Dashboard 页面**

```tsx
// src/pages/Dashboard/index.tsx
import { StatCard } from '@/components/StatCard';

export function Dashboard() {
  return (
    <div className="dashboard">
      <div className="stats-grid">
        <StatCard
          title="总用例数"
          value={stats.testcaseCount}
          trend="+12%"
          icon={<FileTextOutlined />}
          color="blue"
        />
        <StatCard
          title="通过率"
          value={`${stats.passRate}%`}
          trend="+5%"
          icon={<CheckCircleOutlined />}
          color="green"
        />
        {/* ...更多卡片 */}
      </div>

      {/* 其他内容 */}
    </div>
  );
}
```

### 2.2 元素管理优化

**创建 VirtualizedList 组件**

```tsx
// src/components/VirtualizedList.tsx
import { useVirtualizer } from '@tanstack/react-virtual';

interface VirtualizedListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
}

export function VirtualizedList<T>({
  items,
  height,
  itemHeight,
  renderItem,
}: VirtualizedListProps<T>) {
  const parentRef = React.useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan: 5,
  });

  return (
    <div ref={parentRef} style={{ height, overflow: 'auto' }}>
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
              height: `${itemHeight}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem(items[virtualItem.index], virtualItem.index)}
          </div>
        ))}
      </div>
    </div>
  );
}
```

**添加批量操作功能**

```tsx
// 在 Elements 页面添加
const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

const batchDelete = async () => {
  try {
    await Promise.all(selectedRowKeys.map(id => deleteElement(Number(id))));
    message.success(`已删除 ${selectedRowKeys.length} 个元素`);
    setSelectedRowKeys([]);
    queryClient.invalidateQueries({ queryKey: ['elements'] });
  } catch (error) {
    message.error('批量删除失败');
  }
};

// 在工具栏显示
{selectedRowKeys.length > 0 && (
  <Space>
    <Button onClick={batchDelete} danger>
      批量删除 ({selectedRowKeys.length})
    </Button>
  </Space>
)}
```

### 2.3 流程编辑器优化

**安装拖拽库**

```bash
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

**创建可拖拽步骤列表**

```tsx
// src/components/DraggableStepList.tsx
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface DraggableStepListProps {
  steps: Step[];
  onReorder: (oldIndex: number, newIndex: number) => void;
  renderStep: (step: Step, index: number) => React.ReactNode;
}

function SortableItem({ id, children }: { id: string; children: React.ReactNode }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      {children}
    </div>
  );
}

export function DraggableStepList({ steps, onReorder, renderStep }: DraggableStepListProps) {
  const handleDragEnd = (event: any) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      const oldIndex = steps.findIndex(s => s.id === active.id);
      const newIndex = steps.findIndex(s => s.id === over.id);
      onReorder(oldIndex, newIndex);
    }
  };

  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={steps.map(s => s.id)} strategy={verticalListSortingStrategy}>
        {steps.map((step, index) => (
          <SortableItem key={step.id} id={step.id}>
            {renderStep(step, index)}
          </SortableItem>
        ))}
      </SortableContext>
    </DndContext>
  );
}
```

---

## Phase 3: 交互增强 (Week 6-7)

### 3.1 快捷键系统

**创建快捷键Hook**

```tsx
// src/hooks/useHotkeys.ts
import { useEffect } from 'react';

export function useHotkeys(
  keys: string,
  callback: (e: KeyboardEvent) => void,
  options?: { preventDefault?: boolean }
) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      const keyCombinations = keys.split(',').map(k => k.trim().toLowerCase());
      const currentKey = e.key.toLowerCase();

      const match = keyCombinations.some(combo => {
        const parts = combo.split('+');
        const hasMod = parts.includes('mod') || parts.includes('cmd') || parts.includes('ctrl');
        const baseKey = parts.find(p => !['mod', 'cmd', 'ctrl'].includes(p));

        return hasMod && modKey && baseKey === currentKey;
      });

      if (match) {
        if (options?.preventDefault) {
          e.preventDefault();
        }
        callback(e);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [keys, callback, options]);
}
```

**创建快捷键帮助组件**

```tsx
// src/components/HotkeyHelp.tsx
export function HotkeyHelp() {
  const shortcuts = [
    { key: 'Cmd+K', desc: '打开搜索' },
    { key: 'Cmd+N', desc: '新建' },
    { key: 'Cmd+S', desc: '保存' },
    { key: 'Esc', desc: '关闭弹窗' },
  ];

  return (
    <Modal title="快捷键" open={visible} onCancel={onClose}>
      <div className="hotkey-list">
        {shortcuts.map(s => (
          <div key={s.key} className="hotkey-item">
            <kbd>{s.key}</kbd>
            <span>{s.desc}</span>
          </div>
        ))}
      </div>
    </Modal>
  );
}
```

### 3.2 命令面板

**安装 cmdk**

```bash
npm install cmdk
```

**创建命令面板**

```tsx
// src/components/CommandPalette.tsx
import { Command } from 'cmdk';

export function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(open => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return (
    <Command.Dialog open={open} onOpenChange={setOpen}>
      <Command.Content>
        <Command.Input placeholder="输入命令..." />
        <Command.List>
          <Command.Empty>没有找到结果</Command.Empty>
          <Command.Group heading="基础操作">
            <Command.Item onSelect={() => navigate('/elements')}>
              新建元素
            </Command.Item>
            <Command.Item onSelect={() => navigate('/flows')}>
              新建流程
            </Command.Item>
          </Command.Group>
        </Command.List>
      </Command.Content>
    </Command.Dialog>
  );
}
```

### 3.3 全局搜索

**创建搜索服务**

```typescript
// src/services/search.ts
export async function globalSearch(query: string) {
  const response = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}`);
  return response.json();
}
```

**创建搜索组件**

```tsx
// src/components/GlobalSearch.tsx
export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');

  const { data: results } = useQuery({
    queryKey: ['search', search],
    queryFn: () => globalSearch(search),
    enabled: search.length >= 2,
  });

  return (
    <>
      <Input
        placeholder="搜索... (⌘K)"
        onFocus={() => setOpen(true)}
        prefix={<SearchOutlined />}
      />
      <Modal open={open} onCancel={() => setOpen(false)} footer={null}>
        <Input
          size="large"
          placeholder="搜索元素、步骤、流程、用例..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />
        <div className="search-results">
          {results?.elements?.map(item => (
            <div key={item.id} className="search-result-item">
              <AppstoreOutlined />
              <span>{item.name}</span>
            </div>
          ))}
        </div>
      </Modal>
    </>
  );
}
```

---

## Phase 4: 性能与无障碍 (Week 8)

### 4.1 性能优化

**代码分割**

```tsx
// src/App.tsx
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Elements = lazy(() => import('./pages/Elements'));

// 预加载
const preloadRoute = (path: string) => {
  switch (path) {
    case '/elements':
      import('./pages/Elements');
      break;
  }
};

<Sidebar onItemHover={preloadRoute} />
```

**图片优化**

```tsx
// 使用 Next.js Image 或类似组件
import Image from 'next/image';

<Image
  src="/screenshot.png"
  alt="截图"
  width={800}
  height={600}
  loading="lazy"
/>
```

### 4.2 无障碍优化

**添加 ARIA 标签**

```tsx
<Button
  aria-label="新建元素"
  onClick={handleCreate}
>
  <PlusOutlined />
  <span className="sr-only">新建元素</span>
</Button>
```

**焦点管理**

```tsx
// src/hooks/useFocusTrap.ts
export function useFocusTrap(isActive: boolean) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!isActive || !ref.current) return;

    const focusableElements = ref.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleTab);
    firstElement?.focus();

    return () => {
      document.removeEventListener('keydown', handleTab);
    };
  }, [isActive]);

  return ref;
}
```

---

## 📊 进度跟踪

### 使用 GitHub Projects

创建 GitHub Project 跟踪实施进度：

| 任务 | 负责人 | 状态 | 截止日期 |
|------|--------|------|----------|
| 安装依赖 | @dev | ✅ 完成 | Week 1 |
| 配置 Tailwind | @dev | ✅ 完成 | Week 1 |
| 创建基础组件 | @dev | 🔄 进行中 | Week 2 |
| Dashboard 重构 | @design | 📋 计划中 | Week 3 |
| 元素管理优化 | @dev | 📋 计划中 | Week 4 |
| 流程编辑器优化 | @dev | 📋 计划中 | Week 5 |

---

## ✅ 验收标准

### 设计系统

- [ ] 所有颜色使用主题变量
- [ ] 所有间距使用 8px 基准
- [ ] 所有圆角符合设计规范
- [ ] 支持深色模式切换

### 组件

- [ ] 所有组件有 TypeScript 类型
- [ ] 所有组件有单元测试
- [ ] 所有组件有 Storybook 故事
- [ ] 所有组件支持键盘导航

### 页面

- [ ] 所有页面有骨架屏
- [ ] 所有页面有错误处理
- [ ] 所有页面有空状态
- [ ] 所有页面支持响应式

### 性能

- [ ] 首屏加载 < 2s
- [ ] 路由切换 < 500ms
- [ ] 列表滚动流畅（60fps）
- [ ] Lighthouse 分数 > 90

---

## 🐛 常见问题

### Q: Tailwind 样式不生效？

A: 确保 `index.css` 中包含了 `@tailwind` 指令，并且 `tailwind.config.js` 的 `content` 配置正确。

### Q: 虚拟滚动导致样式问题？

A: 确保为虚拟化项目设置固定高度，并使用 `transform` 而非 `top` 定位。

### Q: 拖拽功能不工作？

A: 确保为可拖拽元素设置唯一的 `id`，并且 `DndContext` 包裹了整个列表。

---

**文档版本**: v1.0
**最后更新**: 2026-03-27