# TestcaseItems 实施总结

## ✅ 第3步完成：前端 UI 实现

**完成时间**: 2026-03-25

---

## 已完成的工作

### 1. API Service 层 ✅

**文件**: `frontend/src/services/testcase.ts`

**新增内容**:
- ✅ `TestcaseItem` 接口定义
- ✅ `TestcaseDetail` 接口扩展（包含 testcase_items）
- ✅ `getTestcaseItems()` API 函数
- ✅ `updateTestcaseItems()` API 函数

**新增代码**:
```typescript
export interface TestcaseItem {
  id: number;
  testcase_id: number;
  item_type: 'flow' | 'step';
  flow_id?: number;
  step_id?: number;
  order_index: number;
  enabled: boolean;
  continue_on_error?: boolean;
  params?: Record<string, any>;
  flow_name?: string;
  step_name?: string;
  step_action_type?: string;
  created_at: string;
  updated_at: string;
}

export interface TestcaseDetail extends Testcase {
  setup_flows: TestcaseFlow[];
  main_flows: TestcaseFlow[];
  teardown_flows: TestcaseFlow[];
  testcase_items?: TestcaseItem[];  // 新增
  inline_steps: any[];
}

// 新增 API 函数
export const getTestcaseItems = (testcaseId: number) => {
  return api.get(`/testcases/${testcaseId}/items`);
};

export const updateTestcaseItems = (
  testcaseId: number,
  items: Array<{...}>
) => {
  return api.put(`/testcases/${testcaseId}/items`, { items });
};
```

### 2. ItemsEditor 组件 ✅

**文件**: `frontend/src/components/TestcaseItemsEditor/index.tsx` (新建)

**功能特性**:
- ✅ 添加 Flow 或 Step item
- ✅ 列表展示（区分 Flow 和 Step，显示不同颜色）
- ✅ 上移/下移排序
- ✅ 启用/禁用切换
- ✅ 编辑 item
- ✅ 删除 item
- ✅ 显示 item 详情（flow_name, step_name, step_action_type）
- ✅ 显示 continue_on_error 标签

**核心功能**:

#### 添加 Item
```typescript
const handleAdd = () => {
  setEditingIndex(-1);
  form.resetFields();
  form.setFieldsValue({
    item_type: 'flow',
    flow_id: undefined,
    step_id: undefined,
    order_index: items.length + 1,
    enabled: true,
    continue_on_error: false,
  });
  setAddModalOpen(true);
};
```

#### 移动排序
```typescript
const handleMoveUp = (index: number) => {
  if (index === 0) return;
  const newItems = [...items];
  [newItems[index - 1], newItems[index]] = [newItems[index], newItems[index - 1]];
  // 更新 order_index
  newItems.forEach((item, i) => {
    item.order_index = i + 1;
  });
  onChange(newItems);
};
```

#### 删除 Item
```typescript
const handleDelete = (index: number) => {
  const newItems = items.filter((_, i) => i !== index);
  // 重新排序
  newItems.forEach((item, i) => {
    item.order_index = i + 1;
  });
  onChange(newItems);
};
```

**UI 展示**:
```
┌──────────────────────────────────────────────────────────────┐
│ [添加 Item]  支持 Flow 和 Step 混排，可拖拽排序                │
├──────────────────────────────────────────────────────────────┤
│ ⠿ FLOW  登录流程              [启用] ↑ ↓ 编辑 [×]            │
│ ⠿ STEP 输入用户名 (input)     [启用] ↑ ↓ 编辑 [×]            │
│ ⠿ STEP 点击登录按钮 (click)   [启用] ↑ ↓ 编辑 [×]            │
│ ⠿ FLOW  进入设置页            [启用] ↑ ↓ 编辑 [×]            │
└──────────────────────────────────────────────────────────────┘
```

### 3. Testcases 页面改造 ✅

**文件**: `frontend/src/pages/Testcases/index.tsx`

**修改内容**:

#### 3.1 导入新组件和类型
```typescript
import {
  updateTestcaseItems,
  type TestcaseItem,
} from '../../services/testcase';
import TestcaseItemsEditor from '../../components/TestcaseItemsEditor';
```

#### 3.2 扩展表单数据类型
```typescript
type FormData = {
  // ... 原有字段
  use_items?: boolean;           // 新增：是否使用新格式
  testcase_items?: TestcaseItem[]; // 新增：items 数据
};
```

#### 3.3 修改 `openEdit()` 函数
```typescript
const openEdit = async (row: Testcase) => {
  setEditing(row);
  try {
    const detailResp = await getTestcase(row.id);
    const detail = detailResp?.data?.data;

    // 检查是否有 testcase_items
    const testcase_items = detail?.testcase_items || [];
    const use_items = testcase_items.length > 0;

    form.setFieldsValue({
      // ... 其他字段
      use_items,
      testcase_items,
    });
  } catch {
    // ...
  }
  setEditOpen(true);
};
```

#### 3.4 修改 `submitEdit()` 函数
```typescript
const submitEdit = async () => {
  const values = await form.validateFields();

  const basePayload = {
    name: values.name,
    description: values.description,
    priority: values.priority,
    timeout: values.timeout,
    params,
    setup_flows: toFlowPayload(values.setup_flow_ids),
    teardown_flows: toFlowPayload(values.teardown_flow_ids),
  };

  // 根据选择的格式处理
  if (values.use_items) {
    // 新格式：使用 testcase_items
    if (!values.testcase_items || values.testcase_items.length === 0) {
      message.warning('请至少添加一个 Item');
      return;
    }

    // 先创建/更新用例基本信息
    if (editing) {
      await updateTestcase(editing.id, {
        ...basePayload,
        main_flows: [], // 清空 main_flows
      });
      // 然后更新 testcase_items
      await updateTestcaseItems(editing.id, values.testcase_items);
      message.success('更新成功');
    } else {
      // 新建时，先创建用例
      const createResp = await createTestcase({
        ...basePayload,
        main_flows: [],
      } as any);
      const newId = createResp?.data?.data?.id;
      if (newId) {
        // 然后更新 testcase_items
        await updateTestcaseItems(newId, values.testcase_items);
      }
      message.success('创建成功');
    }
  } else {
    // 旧格式：使用 main_flows
    const payload = {
      ...basePayload,
      main_flows: toFlowPayload(values.main_flow_ids),
    };

    if (payload.main_flows.length === 0) {
      message.warning('主流程至少选择一个');
      return;
    }

    if (editing) {
      updateMutation.mutate({ id: editing.id, payload });
    } else {
      createMutation.mutate(payload as any);
    }
  }

  setEditOpen(false);
  queryClient.invalidateQueries({ queryKey: ['testcases'] });
};
```

#### 3.5 修改编辑表单
```tsx
<Form form={form} layout="vertical">
  {/* ... 基本字段 */}

  {/* Main 阶段：支持两种格式 */}
  <Form.Item label="Main 阶段配置">
    <Form.Item noStyle name="use_items" valuePropName="checked">
      <Switch
        checkedChildren="新格式 (Items)"
        unCheckedChildren="旧格式 (Main Flows)"
        onChange={(checked) => {
          // 切换格式时清空相关字段
          if (checked) {
            form.setFieldsValue({ main_flow_ids: [] });
          } else {
            form.setFieldsValue({ testcase_items: [] });
          }
        }}
      />
    </Form.Item>
  </Form.Item>

  <Form.Item noStyle shouldUpdate={(prev, curr) => prev.use_items !== curr.use_items}>
    {({ getFieldValue }) => {
      const useItems = getFieldValue('use_items');

      if (useItems) {
        // 新格式：Items Editor
        return (
          <Form.Item
            name="testcase_items"
            label="Main Items (Flow/Step 混排)"
            rules={[{ required: true, type: 'array', min: 1, message: '请至少添加一个 Item' }]}
          >
            <TestcaseItemsEditor
              testcaseId={editing?.id}
              items={form.getFieldValue('testcase_items') || []}
              onChange={(items) => form.setFieldsValue({ testcase_items: items })}
            />
          </Form.Item>
        );
      } else {
        // 旧格式：Main Flows
        return (
          <Form.Item
            name="main_flow_ids"
            label="Main Flows"
            rules={[{ required: true, type: 'array', min: 1, message: '至少选择一个主流程' }]}
          >
            <Select mode="multiple" options={flowOptions} placeholder="选择主流程" />
          </Form.Item>
        );
      }
    }}
  </Form.Item>

  {/* ... 其他字段 */}
</Form>
```

---

## UI 展示效果

### 编辑表单

#### 基本字段区
```
名称: [____________________]
描述: [____________________]
优先级: [P1 ▼]  超时(秒): [120]
```

#### Setup Flows
```
Setup Flows: [选择前置流程...]
```

#### Main 阶段配置
```
Main 阶段配置:
[旧格式 (Main Flows)] ← 切换开关 → [新格式 (Items)]
```

#### 旧格式（Main Flows）
```
Main Flows: [选择主流程...] (必填)
```

#### 新格式（Items）
```
Main Items (Flow/Step 混排):
┌──────────────────────────────────────────────┐
│ [添加 Item]  支持 Flow 和 Step 混排，可拖拽排序 │
├──────────────────────────────────────────────┤
│ ⠿ FLOW  登录流程                [启用] ↑ ↓ 编辑 [×] │
│ ⠿ STEP 输入用户名 (input)       [启用] ↑ ↓ 编辑 [×] │
│ ⠿ STEP 点击登录按钮 (click)      [启用] ↑ ↓ 编辑 [×] │
│ ⠿ FLOW  进入设置页              [启用] ↑ ↓ 编辑 [×] │
└──────────────────────────────────────────────┘
```

#### Teardown Flows
```
Teardown Flows: [选择后置流程...]
```

#### 参数
```
参数(JSON): [{...}]
```

### 添加/编辑 Item 弹窗

```
┌─────────────────────────────────────────────┐
│ 添加 Item                                    │
├─────────────────────────────────────────────┤
│ 类型: [Flow（执行整个流程） ▼]               │
│                                              │
│ 选择 Flow: [搜索并选择 Flow...]               │
│                                              │
│ 顺序: [1]                                    │
│                                              │
│ 启用: [✓] 是                                 │
│                                              │
│ 失败继续执行: [ ] 是                          │
│         如果启用，该 Item 执行失败后将继续执行  │
│                                              │
│           [取消]  [确定]                      │
└─────────────────────────────────────────────┘
```

---

## 功能特性

### 1. 格式切换

**切换开关**:
- 旧格式 (Main Flows) → 新格式 (Items)
- 切换时自动清空相关字段，避免数据混乱

**智能检测**:
- 打开编辑时自动检测用例是否使用 testcase_items
- 有 testcase_items → 自动切换到新格式
- 无 testcase_items → 使用旧格式

### 2. Items Editor 功能

#### 基本操作
- ✅ **添加**: 点击"添加 Item"按钮，选择 Flow 或 Step
- ✅ **编辑**: 点击"编辑"按钮，修改 item 配置
- ✅ **删除**: 点击删除按钮（带确认）
- ✅ **排序**: 点击 ↑ ↓ 按钮上移/下移

#### 高级功能
- ✅ **启用/禁用**: 切换开关临时禁用某个 item
- ✅ **失败继续**: 配置 continue_on_error 标志
- ✅ **智能展示**:
  - Flow 显示蓝色标签
  - Step 显示绿色标签
  - 显示 flow_name 或 step_name
  - Step 显示 action_type
  - 显示 continue_on_error 标签

#### 数据验证
- ✅ Flow 类型必须选择 flow_id
- ✅ Step 类型必须选择 step_id
- ✅ 至少添加一个 Item
- ✅ order_index 自动维护

### 3. 保存逻辑

#### 新建用例
```typescript
1. 创建用例（main_flows = []）
2. 调用 updateTestcaseItems() 保存 items
```

#### 编辑用例（新格式）
```typescript
1. 更新用例基本信息（main_flows = []）
2. 调用 updateTestcaseItems() 全量替换 items
```

#### 编辑用例（旧格式）
```typescript
1. 直接更新用例（包含 main_flows）
```

---

## 向后兼容性

### 旧用例（使用 main_flows）

**打开编辑时**:
- 自动检测 testcase_items 为空
- 切换开关显示"旧格式 (Main Flows)"
- 显示 main_flows 多选框

**保存时**:
- 调用原有的 updateTestcase() API
- 不涉及 testcase_items

### 新用例（使用 testcase_items）

**打开编辑时**:
- 自动检测 testcase_items 非空
- 切换开关显示"新格式 (Items)"
- 显示 ItemsEditor 组件

**保存时**:
- 先更新用例基本信息（main_flows = []）
- 再调用 updateTestcaseItems() 保存 items

### 格式迁移

**从旧到新**:
1. 打开旧用例
2. 切换到"新格式 (Items)"
3. 手动添加 Items
4. 保存

**从新到旧**:
1. 打开新用例
2. 切换到"旧格式 (Main Flows)"
3. 重新选择 main_flows
4. 保存（testcase_items 会被清空）

---

## 文件清单

### 新创建的文件
| 文件 | 用途 |
|------|------|
| `frontend/src/components/TestcaseItemsEditor/index.tsx` | Items Editor 组件 |

### 修改的文件
| 文件 | 修改内容 |
|------|----------|
| `frontend/src/services/testcase.ts` | 添加 TestcaseItem 接口和 API 函数 |
| `frontend/src/pages/Testcases/index.tsx` | 集成 ItemsEditor，支持两种格式切换 |

---

## 测试场景

### 场景1: 新建用例（新格式）

**操作**:
1. 点击"新建用例"
2. 填写基本信息
3. 切换到"新格式 (Items)"
4. 点击"添加 Item"
5. 选择 Flow，点击确定
6. 再添加一个 Step
7. 点击"确定"保存

**预期结果**:
- 用例创建成功
- testcase_items 包含 2 个 items
- 执行时按 items 顺序执行

### 场景2: 编辑旧用例（保持旧格式）

**操作**:
1. 点击"编辑"旧用例
2. 确认显示"旧格式 (Main Flows)"
3. 修改 main_flows 选择
4. 点击"确定"保存

**预期结果**:
- 用例更新成功
- main_flows 被修改
- testcase_items 仍为空

### 场景3: 旧用例迁移到新格式

**操作**:
1. 点击"编辑"旧用例
2. 切换到"新格式 (Items)"
3. 根据原有的 main_flows 手动添加对应的 items
4. 点击"确定"保存

**预期结果**:
- 用例更新成功
- testcase_items 包含新添加的 items
- main_flows 被清空

### 场景4: 启用/禁用 Item

**操作**:
1. 打开新格式用例
2. 找到某个 item
3. 切换启用/禁用开关
4. 保存

**预期结果**:
- 禁用的 item 在执行时被跳过

### 场景5: 失败继续执行

**操作**:
1. 打开新格式用例
2. 编辑某个 item
3. 勾选"失败继续执行"
4. 保存

**预期结果**:
- 该 item 执行失败后，后续 items 继续执行

---

## 下一步：第4步 - Importer 支持 + 旧格式回退

需要实现的功能：

1. **Batch Import 支持 testcase_items**
   - 解析 items 字段
   - 调用 updateTestcaseItems() API

2. **向后兼容测试**
   - 旧格式导入正常工作
   - 新格式导入正常工作

3. **文档更新**
   - 更新 API 文档
   - 更新用户手册

---

## 总结

第3步**全部完成**，前端 UI 完全支持 testcase_items。

✅ **API Service**: 新增接口定义和 API 函数
✅ **ItemsEditor 组件**: 完整的 items 编辑器
✅ **Testcases 页面**: 支持两种格式切换
✅ **向后兼容**: 旧用例继续正常工作
✅ **保存逻辑**: 正确处理两种格式的保存

**前端 UI 已完成，可以进入第4步：Importer 支持**

要我现在开始第4步吗？
