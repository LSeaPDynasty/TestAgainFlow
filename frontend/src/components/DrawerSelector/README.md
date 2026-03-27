# DrawerSelector 侧边抽屉选择器

## 功能特性

- ✅ 替代传统Select下拉框
- ✅ 点击后弹出侧边抽屉（左侧/右侧可选）
- ✅ 支持搜索过滤
- ✅ 支持单选/多选
- ✅ 美观的选中状态
- ✅ 支持自定义触发器

## 基础用法

### 单选模式

```typescript
import DrawerSelector from '@/components/DrawerSelector';

<DrawerSelector
  options={[
    { value: '1', label: '选项1' },
    { value: '2', label: '选项2' },
    { value: '3', label: '选项3' },
  ]}
  value={selectedValue}
  onChange={(value) => setSelectedValue(value)}
  placeholder="请选择"
  title="选择选项"
/>
```

### 多选模式

```typescript
<DrawerSelector
  multiple
  options={options}
  value={selectedValues}
  onChange={(values) => setSelectedValues(values)}
  placeholder="请选择多个"
  title="选择多个选项"
/>
```

### 带搜索

```typescript
<DrawerSelector
  searchable
  options={options}
  onSearch={(keyword) => {
    // 执行搜索
    console.log('搜索:', keyword);
  }}
  searchPlaceholder="搜索选项..."
/>
```

### 自定义触发器

```typescript
<DrawerSelector
  trigger={
    <Button icon={<PlusOutlined />}>
      添加选项
    </Button>
  }
  options={options}
  value={value}
  onChange={onChange}
/>
```

### 从右侧弹出

```typescript
<DrawerSelector
  placement="right"
  drawerWidth={600}
  options={options}
  value={value}
  onChange={onChange}
/>
```

### 从左侧弹出

```typescript
<DrawerSelector
  placement="left"
  options={options}
  value={value}
  onChange={onChange}
/>
```

## API

### DrawerSelectorProps

| 属性 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| options | 选项数组 | DrawerSelectorOption[] | [] |
| value | 选中的值 | string \| number \| array | - |
| onChange | 值变化回调 | function(value) | - |
| multiple | 是否多选 | boolean | false |
| disabled | 是否禁用 | boolean | false |
| searchable | 是否可搜索 | boolean | true |
| placeholder | 占位文本 | string | '请选择' |
| title | 抽屉标题 | string | '请选择' |
| drawerWidth | 抽屉宽度 | number | 480 |
| placement | 弹出位置 | 'left' \| 'right' | 'right' |
| trigger | 自定义触发器 | ReactNode | - |
| onSearch | 搜索回调 | function(keyword) | - |
| loading | 加载状态 | boolean | false |
| allowClear | 是否允许清除 | boolean | true |

### DrawerSelectorOption

| 属性 | 说明 | 类型 | 必填 |
|------|------|------|------|
| value | 选项值 | string \| number | 是 |
| label | 显示文本 | string | 是 |
| description | 描述信息 | string | 否 |
| disabled | 是否禁用 | boolean | 否 |
| extra | 额外内容 | ReactNode | 否 |

## 替换现有Select示例

### 替换前（Select）

```typescript
<Select
  style={{ width: 200 }}
  value={selectedScreen}
  onChange={setSelectedScreen}
  options={screens.map(s => ({
    value: s.id,
    label: s.name,
  }))}
  placeholder="请选择Screen"
/>
```

### 替换后（DrawerSelector）

```typescript
<DrawerSelector
  value={selectedScreen}
  onChange={setSelectedScreen}
  options={screens.map(s => ({
    value: s.id,
    label: s.name,
    description: s.description,
  }))}
  placeholder="请选择Screen"
  title="选择Screen"
  drawerWidth={400}
  placement="right"
/>
```

## 优势

1. **更大的展示空间** - 不再受限于下拉框的小窗口
2. **更好的搜索体验** - 专门的搜索框，实时过滤
3. **更清晰的选择状态** - 明显的选中标识
4. **更美观** - 现代化的抽屉设计
5. **更易用** - 点击区域大，操作直观
6. **支持复杂场景** - 多选、搜索、自定义渲染等
