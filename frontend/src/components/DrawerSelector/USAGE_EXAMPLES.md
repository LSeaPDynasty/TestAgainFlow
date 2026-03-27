# DrawerSelector 全局主题系统使用指南

## 📦 已创建的文件

```
frontend/src/components/DrawerSelector/
├── index.tsx           # 组件实现
├── styles.css          # 全局样式（4种主题）
├── theme.ts            # 主题配置
├── config.ts           # 全局和页面级配置
└── USAGE_EXAMPLES.md    # 本文档
```

## 🎨 可用主题

### 1. **默认主题** (default)
- 经典Ant Design风格
- 灰白色调
- 适合大多数场景

### 2. **现代主题** (modern)
- 渐变紫色
- 更大更舒适的触控区域
- 阴影效果更强

### 3. **深色主题** (dark)
- 深灰色调
- 护眼模式
- 适合暗色环境

### 4. **紧凑主题** (compact)
- 更小的间距
- 节省屏幕空间
- 适合数据密集型页面

## 🚀 快速开始

### 1. 导入样式

在主入口文件导入样式：

```typescript
// src/App.tsx 或 src/main.tsx
import './components/DrawerSelector/styles.css';
```

### 2. 基础使用

```tsx
import DrawerSelector from '@/components/DrawerSelector';

function MyComponent() {
  const [selectedValue, setSelectedValue] = useState<number>();

  return (
    <DrawerSelector
      options={[
        { value: 1, label: '选项1', description: '这是选项1的描述' },
        { value: 2, label: '选项2', description: '这是选项2的描述' },
        { value: 3, label: '选项3', description: '这是选项3的描述' },
      ]}
      value={selectedValue}
      onChange={setSelectedValue}
      placeholder="请选择"
      title="选择选项"
    />
  );
}
```

## 🎯 主题应用方式

### 方式1: 全局统一主题（推荐）

在App.tsx中设置全局主题：

```tsx
import { DRAWER_SELECTOR_DEFAULT_CONFIG } from './components/DrawerSelector/config';

// 修改默认主题
DRAWER_SELECTOR_DEFAULT_CONFIG.theme = 'modern';

// 所有DrawerSelector组件都会使用modern主题
```

### 方式2: 页面级主题

为特定页面设置主题：

```tsx
import { getPageSelectorConfig, applyTheme } from '@/components/DrawerSelector/config';

const config = applyTheme(
  getPageSelectorConfig('steps', 'screen'),
  'modern'
);

<DrawerSelector {...config} options={screens} />
```

### 方式3: 组件级主题

为单个组件设置主题：

```tsx
<DrawerSelector
  theme="modern"
  options={options}
  value={value}
  onChange={onChange}
/>
```

## 📋 实际应用示例

### 示例1: Steps页面 - Screen选择器

```tsx
import { getPageSelectorConfig } from '@/components/DrawerSelector/config';

const screenConfig = getPageSelectorConfig('steps', 'screen');

<DrawerSelector
  {...screenConfig}
  options={screens.map(s => ({
    value: s.id,
    label: s.name,
    description: `元素数量: ${s.element_count}`,
  }))}
  value={selectedScreen}
  onChange={setSelectedScreen}
  placeholder="请选择Screen"
  title="选择Screen"
/>
```

### 示例2: 多选模式（Tag选择）

```tsx
import { getPageSelectorConfig } from '@/components/DrawerSelector/config';

const tagConfig = getPageSelectorConfig('testcases', 'tag');

<DrawerSelector
  {...tagConfig}
  multiple
  options={tags.map(t => ({
    value: t.id,
    label: t.name,
    extra: <Tag color={t.color}>{t.name}</Tag>,
  }))}
  value={selectedTags}
  onChange={setSelectedTags}
  placeholder="选择标签"
  title="选择标签"
/>
```

### 示例3: 带搜索的分页选择器

```tsx
const [page, setPage] = useState(1);
const [pageSize, setPageSize] = useState(20);
const [searchKeyword, setSearchKeyword] = useState('');

<DrawerSelector
  options={paginatedOptions}
  value={value}
  onChange={onChange}
  pagination={{
    current: page,
    pageSize: pageSize,
    total: totalCount,
    onChange: setPage,
  }}
  onSearch={(keyword) => {
    setSearchKeyword(keyword);
    refetchData(keyword, page, pageSize);
  }}
  loading={isLoading}
/>
```

### 示例4: 自定义触发器样式

```tsx
<DrawerSelector
  trigger={
    <Button
      type="primary"
      icon={<PlusOutlined />}
      size="large"
    >
      添加选项
    </Button>
  }
  options={options}
  value={value}
  onChange={onChange}
  drawerWidth={600}
  placement="left"
/>
```

## 🎨 高级自定义

### 自定义选项渲染

```tsx
<DrawerSelector
  options={options}
  renderExtra={(option) => (
    <Space>
      <Tag color="blue">{option.category}</Tag>
      <Tag color="green">{option.status}</Tag>
      <Button size="small">查看</Button>
    </Space>
  )}
  value={value}
  onChange={onChange}
/>
```

### 不同方向弹出

```tsx
{/* 从右侧弹出（默认） */}
<DrawerSelector placement="right" />

{/* 从左侧弹出 */}
<DrawerSelector placement="left" />
```

### 响应式宽度

```tsx
<DrawerSelector
  drawerWidth={isMobile ? '100vw' : 480}
  placement={isMobile ? 'bottom' : 'right'}
/>
```

## 🔧 配置说明

### 全局配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| theme | 默认主题 | 'default' |
| drawerWidth | 抽屉宽度 | 480 |
| placement | 弹出方向 | 'right' |
| searchable | 是否可搜索 | true |
| allowClear | 是否可清除 | true |
| showCount | 是否显示数量 | true |
| animationDuration | 动画时长(ms) | 300 |
| pageSize | 分页大小 | 20 |

### 页面级配置

不同页面有专门的配置：

- `STEPS_PAGE_SELECTOR_CONFIG` - Steps页面
- `FLOWS_PAGE_SELECTOR_CONFIG` - Flows页面
- `TESTCASES_PAGE_SELECTOR_CONFIG` - Testcases页面
- `ELEMENTS_PAGE_SELECTOR_CONFIG` - Elements页面
- `SUITES_PAGE_SELECTOR_CONFIG` - Suites页面

### 组件Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| options | DrawerSelectorOption[] | [] | 选项数组 |
| value | string\|number\|array | - | 选中的值 |
| onChange | function | - | 值变化回调 |
| multiple | boolean | false | 是否多选 |
| disabled | boolean | false | 是否禁用 |
| searchable | boolean | true | 是否可搜索 |
| loading | boolean | false | 加载状态 |
| placeholder | string | '请选择' | 占位文本 |
| title | string | '请选择' | 抽屉标题 |
| drawerWidth | number | 480 | 抽屉宽度 |
| placement | 'left'\|'right' | 'right' | 弹出方向 |
| theme | string | 'default' | 主题名称 |
| pagination | object | - | 分页配置 |
| onSearch | function | - | 搜索回调 |
| onRefresh | function | - | 刷新回调 |
| trigger | ReactNode | - | 自定义触发器 |
| renderExtra | function | - | 自定义额外内容 |

## 💡 最佳实践

### 1. 统一使用页面级配置

```tsx
// ✅ 推荐
import { getPageSelectorConfig } from '@/components/DrawerSelector/config';

const config = getPageSelectorConfig('steps', 'screen');
<DrawerSelector {...config} />

// ❌ 不推荐
<DrawerSelector drawerWidth={400} placement="right" searchable={true} />
```

### 2. 使用语义化的placeholder

```tsx
// ✅ 好
<DrawerSelector placeholder="请选择Screen" />
<DrawerSelector placeholder="请选择操作类型" />

// ❌ 不好
<DrawerSelector placeholder="请选择" />
```

### 3. 提供有意义的描述

```tsx
options={screens.map(s => ({
  value: s.id,
  label: s.name,
  description: `包含 ${s.element_count} 个元素`,
})}
```

### 4. 合理设置抽屉宽度

- **简单选择**: 360-400px
- **带描述的选择**: 440-480px
- **带额外内容**: 500-600px
- **移动端**: 100vw

### 5. 选择合适的弹出方向

- **大多数场景**: right（从右弹出，不遮挡内容）
- **编辑表单**: left（从左弹出，靠近表单）
- **移动端**: bottom（从底部弹出，符合习惯）

## 🎁 下一步

现在你有了：

1. ✅ DrawerSelector组件
2. ✅ 4种预设主题
3. ✅ 全局配置系统
4. ✅ 页面级配置

需要我帮你：

**A. 立即应用到Steps页面** - 替换所有Select下拉框

**B. 创建主题切换器** - 让用户可以实时切换主题

**C. 批量替换其他页面** - Flows/Testcases/Elements/Suites

**D. 优化动画和交互** - 添加快捷键、虚拟滚动等

选择哪个？
