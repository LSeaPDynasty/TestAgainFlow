# Dashboard 仪表盘 - 设计文档

## 📋 概述

全新设计的仪表盘页面，提供项目概览、实时监控和快速操作功能。

## ✨ 特性

### 1. 核心指标卡片

- **测试用例**: 显示总用例数，带趋势指示器
- **通过率**: 显示测试通过率，带进度条
- **总执行数**: 显示累计执行次数
- **在线设备**: 显示设备状态，可点击查看详情

### 2. 资源统计

- 元素总数
- 步骤总数
- 流程总数

### 3. 执行趋势图

- 使用 Recharts 绘制面积图
- 显示通过/失败趋势
- 支持时间范围筛选

### 4. 失败排行榜

- Top 10 失败用例
- 可视化进度条
- 带奖牌图标

### 5. 最近活动

- 实时显示执行记录
- 状态图标（成功/失败/运行中）
- 点击可查看详情

### 6. 快速操作

- 创建用例
- 执行测试
- 管理设备
- 环境配置
- 流程管理

## 🎨 设计亮点

### 视觉效果

- **渐变背景**: 每个卡片使用渐变色背景
- **悬停效果**: 卡片悬停时提升和阴影效果
- **图标动画**: 图标悬停时放大效果
- **流畅过渡**: 所有交互都有平滑过渡

### 颜色系统

| 用途 | 颜色 | 说明 |
|------|------|------|
| 主要信息 | 蓝色 | 核心数据 |
| 成功/通过 | 绿色 | 积极状态 |
| 警告/注意 | 黄色 | 需要关注 |
| 失败/错误 | 红色 | 消极状态 |
| 中性信息 | 灰色 | 辅助信息 |

### 响应式设计

- **桌面** (> 1024px): 4列布局
- **平板** (768px - 1024px): 2列布局
- **移动** (< 768px): 单列布局

## 📊 组件说明

### StatCard

统计卡片组件，显示关键指标。

```tsx
<StatCard
  title="测试用例"
  value={stats.testcaseCount}
  icon="📋"
  color="blue"
  trend="+12%"
  description="总用例数"
/>
```

**Props**:

| Prop | 类型 | 说明 |
|------|------|------|
| title | string | 卡片标题 |
| value | string \| number | 显示的数值 |
| icon | string | 图标（支持 emoji） |
| color | ColorType | 颜色主题 |
| trend | string | 趋势（如 "+12%"） |
| description | string | 描述文字 |
| showProgress | boolean | 是否显示进度条 |
| progress | number | 进度值 (0-100) |
| compact | boolean | 紧凑模式 |

### TrendChart

执行趋势图表组件。

```tsx
<TrendChart data={trendData} />
```

**数据格式**:

```typescript
{
  date: string;  // "3月20日"
  pass: number;  // 通过数量
  fail: number;  // 失败数量
}
```

### ActivityFeed

活动时间线组件，显示最近执行记录。

```tsx
<ActivityFeed activities={recentRuns} />
```

### QuickActions

快速操作组件，提供常用功能入口。

```tsx
<QuickActions />
```

### FailureRanking

失败排行榜组件。

```tsx
<FailureRanking data={failureRanking} />
```

### DeviceStatusCard

设备状态卡片组件。

```tsx
<DeviceStatusCard
  online={3}
  total={5}
  devices={devicesList}
/>
```

## 🚀 性能优化

### 1. 自动刷新

- 设备状态: 每 10 秒刷新
- 统计数据: 每 30 秒刷新

### 2. 数据缓存

使用 React Query 缓存数据，减少不必要的请求。

### 3. 懒加载

图表组件按需加载，提升首屏速度。

## 🎯 交互设计

### 点击事件

1. **设备卡片**: 点击打开设备列表弹窗
2. **活动项**: 点击跳转到执行详情
3. **快速操作**: 点击跳转到对应页面

### 悬停效果

- 卡片提升: `hover:-translate-y-1`
- 阴影增强: `hover:shadow-lg`
- 图标放大: `hover:scale-110`

## 📱 响应式断点

```css
/* 移动设备 */
@media (max-width: 576px) { }

/* 平板设备 */
@media (min-width: 577px) and (max-width: 1024px) { }

/* 桌面设备 */
@media (min-width: 1025px) { }
```

## 🔧 自定义配置

### 修改颜色主题

编辑 `Dashboard.css` 中的颜色变量:

```css
.stat-card {
  --card-bg: linear-gradient(...);
  --card-border: #e5e7eb;
}
```

### 修改刷新间隔

编辑 `Dashboard/index.tsx`:

```typescript
refetchInterval: 30000, // 30秒
refetchInterval: 10000, // 10秒
```

## 📝 未来计划

- [ ] 添加更多图表类型（饼图、柱状图）
- [ ] 支持自定义仪表盘布局
- [ ] 添加数据导出功能
- [ ] 支持实时数据推送（WebSocket）
- [ ] 添加对比功能（不同时间段对比）

## 🐛 已知问题

1. **趋势图数据**: 当前使用模拟数据，需要接入真实 API
2. **性能**: 大量设备时可能影响性能，考虑虚拟滚动

## 💡 使用建议

1. **首次访问**: 自动刷新设备状态
2. **定期查看**: 查看"失败Top 10"优化用例
3. **快速操作**: 使用快速操作按钮提升效率
4. **监控设备**: 定期检查设备在线状态

---

**最后更新**: 2026-03-27
**维护者**: TestFlow Team
