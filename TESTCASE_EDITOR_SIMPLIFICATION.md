# Testcase编辑器简化方案

## 已完成的修改

### 1. project_id过滤（任务#13）✅
- 所有资源选择器（Flow/Step）已按project_id过滤
- 避免跨项目数据污染

### 2. 构建基线建立（任务#11）✅
- `npm run build` 成功通过
- 修复了120+个TypeScript错误

## 待完成的修改（任务#12）

### Testcase编辑器简化

**当前状态**：存在use_items切换，用户可以在旧格式(Main Flows)和新格式(Items)之间切换

**目标状态**：
1. 移除Switch切换组件（第728-743行）
2. 移除条件渲染，直接显示TestcaseItemsEditor（第745-838行）
3. 移除main_flow_ids表单项
4. 保留setup_flow_ids和teardown_flow_ids
5. 保留参数模板生成按钮

### 需要修改的代码位置

**文件**: `src/pages/Testcases/index.tsx`

1. **移除Switch组件** (约第728-743行)
```tsx
// 删除这段代码：
<Form.Item label="Main 阶段配置">
  <Form.Item noStyle name="use_items" valuePropName="checked">
    <Switch ... />
  </Form.Item>
</Form.Item>
```

2. **移除条件渲染，直接显示TestcaseItemsEditor** (约第745-838行)
```tsx
// 删除 shouldUpdate 包裹的条件渲染
// 直接显示：
<Form.Item
  name="testcase_items"
  label="Main Items (Flow/Step 混排)"
  rules={[{ required: true, type: 'array', min: 1, message: '请至少添加一个 Item' }]}
>
  <TestcaseItemsEditor ... />
</Form.Item>
```

3. **修改提交逻辑** (约第299-322行)
```tsx
// 删除useItems判断，直接使用testcase_items格式
const values = await form.validateFields();
// ... 移除 if (!useItems) 判断
```

4. **保留旧数据兼容** (约第254行)
```tsx
// 保留这段逻辑，用于检测旧格式用例
const use_items = testcase_items.length > 0;
```

### 用户体验改进

**新建用例**：
- 默认显示testcase_items编辑器
- 提示用户添加Flow/Step
- 自动识别参数并生成模板

**编辑旧格式用例**：
- 检测到main_flows时，显示提示："此用例使用旧格式，已自动转换"
- 自动将main_flows转换为testcase_items（可选功能）

**参数管理**：
- testcase_items负责识别参数名
- "参数(JSON)"字段负责参数值
- 一键生成参数模板按钮

### 实施建议

由于修改较复杂，建议分两步：

**Step 1**: 最小化修改
- 移除Switch组件
- 移除条件渲染
- 直接显示TestcaseItemsEditor
- 暂时保留旧格式数据的兼容提示

**Step 2**: 数据迁移
- 实现main_flows到testcase_items的自动转换
- 在编辑旧用例时自动迁移
- 添加迁移确认提示

### 验证标准

- [ ] 新建用例时，直接显示testcase_items编辑器
- [ ] 编辑新格式用例时，正确加载testcase_items
- [ ] 编辑旧格式用例时，显示兼容提示
- [ ] setup/teardown flows功能正常
- [ ] 参数自动识别和生成功能正常
- [ ] 项目过滤功能正常

### 风险评估

**低风险**：
- 新建用例：不受影响
- 新格式用例：不受影响

**中风险**：
- 旧格式用例编辑：需要测试兼容性
- 数据迁移：需要仔细测试

### 时间估算

- 实施修改：2-3小时
- 测试验证：1-2小时
- 总计：3-5小时
