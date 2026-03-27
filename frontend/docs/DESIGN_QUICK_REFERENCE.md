# TestFlow 设计系统快速参考

> 本文档提供设计系统的快速查阅，包含常用Token和代码片段

---

## 🎨 色彩速查

### 品牌色

```
Primary: #1677FF (主色)
Hover:   #4096FF
Active:  #0958D9
```

### 语义色

```
Success: #52C41A
Warning: #FAAD14
Error:   #FF4D4F
Info:    #1677FF
```

### 优先级色

```
P0: #FF4D4F (红色)
P1: #FAAD14 (橙色)
P2: #FADB14 (黄色)
P3: #8C8C8C (灰色)
```

### 中性色

```
Gray-50:  #FAFAFA (背景)
Gray-100: #F5F5F5 (次级背景)
Gray-200: #E8E8E8 (边框)
Gray-500: #8C8C8C (次级文本)
Gray-700: #434343 (标题文本)
Gray-900: #1F1F1F (最强文本)
```

---

## 📏 间距速查

```
0:  0
1:  4px
2:  8px
3:  12px
4:  16px
5:  20px
6:  24px
8:  32px
12: 48px
16: 64px
```

---

## 🔤 字体速查

```
xs:   12px (辅助文本)
sm:   14px (正文)
base: 16px (默认)
lg:   18px (小标题)
xl:   20px (标题)
2xl:  24px (大标题)
3xl:  30px (页面标题)
```

---

## 📐 圆角速查

```
sm:   4px (Tag, Badge)
base: 8px (Card, Button)
lg:   12px (大卡片)
xl:   16px (Modal)
full: 9999px (圆形)
```

---

## 💻 常用代码片段

### 1. 合并类名

```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 使用
<div className={cn('base-class', isActive && 'active-class')} />
```

### 2. 防抖Hook

```typescript
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

// 使用
const searchTerm = useDebounce(searchInput, 300);
```

### 3. 快捷键Hook

```typescript
import { useEffect } from 'react';

export function useHotkeys(
  key: string,
  callback: (e: KeyboardEvent) => void,
  options?: { preventDefault?: boolean }
) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      if (modKey && e.key.toLowerCase() === key.toLowerCase()) {
        if (options?.preventDefault) {
          e.preventDefault();
        }
        callback(e);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [key, callback, options]);
}

// 使用
useHotkeys('k', () => {
  setOpenSearch(true);
}, { preventDefault: true });
```

### 4. 乐观更新Hook

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useOptimisticMutation<T>(
  mutationFn: (data: T) => Promise<any>,
  queryKey: string[]
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: T) => {
      // 乐观更新
      queryClient.setQueryData(queryKey, (old: any) => [
        ...(old || []),
        { ...data, id: `temp-${Date.now()}`, isPending: true },
      ]);

      try {
        const result = await mutationFn(data);
        queryClient.invalidateQueries({ queryKey });
        return result;
      } catch (error) {
        // 失败回滚
        queryClient.invalidateQueries({ queryKey });
        throw error;
      }
    },
  });
}

// 使用
const createMutation = useOptimisticMutation(
  (data) => createElement(data),
  ['elements']
);
```

### 5. 格式化时间

```typescript
export function formatTime(date: string | Date): string {
  const d = new Date(date);
  const now = new Date();
  const diff = now.getTime() - d.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;

  return d.toLocaleDateString();
}

// 使用
<span>{formatTime(createdAt)}</span>
```

### 6. 格式化文件大小

```typescript
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

// 使用
<span>{formatBytes(fileSize)}</span>
```

---

## 🧩 组件模板

### StatCard 模板

```tsx
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
  return (
    <div className={cn(
      'stat-card',
      `stat-card-${color}`
    )}>
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
    </div>
  );
}
```

### EmptyState 模板

```tsx
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon">{icon}</div>}
      <div className="empty-state-title">{title}</div>
      {description && (
        <div className="empty-state-description">{description}</div>
      )}
      {action && (
        <button
          className="empty-state-action"
          onClick={action.onClick}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
```

---

## 🎯 常用CSS类

### Flexbox

```css
/* 居中 */
.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 两端对齐 */
.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 垂直居中 */
.flex-items-center {
  display: flex;
  align-items: center;
}
```

### 文本

```css
/* 文本截断 */
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 多行文本截断 */
.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

### 滚动条

```css
/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
```

---

## 🔧 Tailwind 配置

```javascript
// tailwind.config.js
module.exports = {
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
      spacing: {
        18: '4.5rem',
        88: '22rem',
        128: '32rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
};
```

---

## 📋 Checklist

### 组件开发Checklist

- [ ] 支持深色模式
- [ ] 支持键盘导航
- [ ] 添加ARIA标签
- [ ] 添加loading状态
- [ ] 添加error状态
- [ ] 添加empty状态
- [ ] 支持自定义className
- [ ] 添加TypeScript类型
- [ ] 添加单元测试
- [ ] 添加Storybook故事

### 页面开发Checklist

- [ ] 响应式布局
- [ ] 骨架屏加载
- [ ] 错误处理
- [ ] 空状态处理
- [ ] 权限控制
- [ ] 面包屑导航
- [ ] 页面标题
- [ ] 快捷键支持
- [ ] 性能优化（虚拟滚动/懒加载）

---

## 📚 相关文档

- [完整设计系统](./DESIGN_SYSTEM_2026.md)
- [组件库文档](./COMPONENTS.md)
- [API文档](./API.md)

---

**最后更新**: 2026-03-27