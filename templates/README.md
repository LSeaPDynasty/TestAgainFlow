# TestFlow 快速导入功能

## 功能概述

TestFlow快速导入功能支持批量导入界面和元素，支持JSON和YAML两种格式。可以快速将外部测试资源的元素定义导入到TestFlow平台。

## 导入模式

### 1. 完整导入模式（界面+元素）

同时导入界面和元素，自动创建界面并添加元素。

**文件格式：**
```json
{
  "version": "1.0",
  "screens": [
    {
      "name": "登录页面",
      "activity": "com.example.app.MainActivity",
      "description": "用户登录界面",
      "elements": [
        {
          "name": "用户名输入框",
          "description": "输入用户名的输入框",
          "locators": [
            {
              "type": "resource-id",
              "value": "com.example.app:id/username",
              "priority": 1
            }
          ]
        }
      ]
    }
  ]
}
```

### 2. 元素导入模式（仅元素）

将元素导入到已存在的界面。

**文件格式：**
```json
{
  "version": "1.0",
  "target_screen": "登录页面",
  "elements": [
    {
      "name": "用户名输入框",
      "description": "输入用户名的输入框",
      "locators": [
        {
          "type": "resource-id",
          "value": "com.example.app:id/username",
          "priority": 1
        }
      ]
    }
  ]
}
```

## 支持的定位符类型

| 类型 | 说明 | 优先级建议 |
|------|------|-----------|
| `resource-id` | 通过资源ID定位（推荐，最稳定） | 1 |
| `text` | 通过文本内容定位 | 1-2 |
| `xpath` | 通过XPath表达式定位（灵活但可能不稳定） | 2-3 |
| `content-desc` | 通过content-desc属性定位 | 2-3 |
| `hint` | 通过hint属性定位 | 2-3 |
| `class` | 通过class属性定位 | 3 |
| `package` | 通过package属性定位 | 3 |

## 导入选项

- **跳过已存在的界面和元素**：如果界面或元素已存在，则跳过不导入
- **自动创建不存在的界面**：如果界面不存在，自动创建

## 使用方法

### 方法1：通过界面管理页面

1. 进入"界面管理"页面
2. 点击"批量导入"按钮
3. 下载模板文件（JSON或YAML格式）
4. 根据模板填写数据
5. 上传文件并点击"开始导入"

### 方法2：通过API直接调用

```bash
# 批量导入
curl -X POST http://localhost:8000/api/v1/import/bulk \
  -H "Content-Type: application/json" \
  -d @import_data.json

# 元素导入
curl -X POST http://localhost:8000/api/v1/import/elements \
  -H "Content-Type: application/json" \
  -d @elements_data.json

# 文件上传导入
curl -X POST http://localhost:8000/api/v1/import/upload \
  -F "file=@import_data.json" \
  -F "skip_existing=true" \
  -F "create_screens=true"
```

## 模板下载

可以通过以下方式下载模板：

### API方式

```bash
# JSON模板
curl http://localhost:8000/api/v1/import/template/json -o import_template.json

# YAML模板
curl http://localhost:8000/api/v1/import/template/yaml -o import_template.yaml

# 元素模板
curl http://localhost:8000/api/v1/import/template/elements-only -o elements_only_template.json
```

### 前端界面

在"界面管理"页面点击"批量导入"按钮，选择对应的模板下载。

## 导入结果说明

导入完成后会显示以下信息：

- **创建界面数**：成功创建的界面数量
- **创建元素数**：成功创建的元素数量
- **跳过项目数**：因已存在而跳过的界面/元素数量
- **错误信息**：导入过程中遇到的错误

## 示例数据

### 示例1：登录页面

```json
{
  "version": "1.0",
  "screens": [
    {
      "name": "登录页面",
      "activity": "com.example.app.MainActivity",
      "description": "用户登录界面",
      "elements": [
        {
          "name": "用户名输入框",
          "description": "输入用户名的输入框",
          "locators": [
            {
              "type": "resource-id",
              "value": "com.example.app:id/username",
              "priority": 1
            },
            {
              "type": "xpath",
              "value": "//*[@text='请输入用户名']",
              "priority": 2
            }
          ]
        },
        {
          "name": "密码输入框",
          "description": "输入密码的输入框",
          "locators": [
            {
              "type": "resource-id",
              "value": "com.example.app:id/password",
              "priority": 1
            },
            {
              "type": "xpath",
              "value": "//*[@text='请输入密码']",
              "priority": 2
            }
          ]
        },
        {
          "name": "登录按钮",
          "description": "点击登录的按钮",
          "locators": [
            {
              "type": "resource-id",
              "value": "com.example.app:id/login_btn",
              "priority": 1
            },
            {
              "type": "text",
              "value": "登录",
              "priority": 2
            }
          ]
        }
      ]
    }
  ]
}
```

### 示例2：首页

```yaml
version: "1.0"
screens:
  - name: "首页"
    activity: "com.example.app.HomeActivity"
    description: "应用首页"
    elements:
      - name: "搜索框"
        description: "顶部搜索框"
        locators:
          - type: "resource-id"
            value: "com.example.app:id/search_input"
            priority: 1
          - type: "hint"
            value: "搜索"
            priority: 2
      - name: "消息图标"
        description: "右上角消息图标"
        locators:
          - type: "resource-id"
            value: "com.example.app:id/message_icon"
            priority: 1
          - type: "content-desc"
            value: "消息"
            priority: 2
```

## 常见问题

### Q1: 导入失败怎么办？

A: 检查以下几点：
1. 文件格式是否正确（JSON或YAML）
2. 必填字段是否填写完整
3. 定位符格式是否正确
4. 界面名称是否与现有界面冲突（当不启用"跳过已存在"时）

### Q2: 支持哪些定位符类型？

A: 支持 `resource-id`, `text`, `xpath`, `content-desc`, `hint`, `class`, `package` 等类型。

### Q3: 如何设置定位符优先级？

A: `priority` 值越小优先级越高，建议将最稳定的定位符设置为 priority: 1。

### Q4: 导入的元素如何验证？

A: 导入完成后，可以在"元素管理"页面查看导入的元素，并使用"测试元素"功能验证定位符是否正确。

### Q5: 能否更新已存在的元素？

A: 当前版本不支持更新，如需更新元素，请先删除原元素再导入，或在界面上手动编辑。

## 技术支持

如有问题，请查看TestFlow文档或联系技术支持团队。
