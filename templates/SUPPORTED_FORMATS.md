# TestFlow 导入格式说明

TestFlow 支持多种格式的导入文件，系统会自动识别并转换为标准格式。

## 格式1: TestFlow 标准格式（推荐）

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

## 格式2: PageInfo 格式（自动转换）

```json
{
  "pageInfo": {
    "pageName": "登录页面",
    "activity": "com.example.app.MainActivity"
  },
  "elements": [
    {
      "name": "用户名输入框",
      "resourceId": "com.example.app:id/username",
      "xpath": "//*[@text='用户名']"
    }
  ]
}
```

**转换规则**:
- `pageInfo.pageName` → `screens[0].name`
- `elements` 数组直接映射
- `resourceId` → `locators[0].type="resource-id"`
- `xpath` → `locators[1].type="xpath"`

## 格式3: 纯元素列表格式

```json
{
  "elements": [
    {
      "name": "登录按钮",
      "locators": [
        {
          "type": "text",
          "value": "登录",
          "priority": 1
        }
      ]
    }
  ]
}
```

**转换规则**:
- 自动创建名为"导入的界面"的screen
- 所有元素导入到该screen下

## 格式4: 元素导入模式（导入到已有界面）

```json
{
  "version": "1.0",
  "target_screen": "登录页面",
  "elements": [
    {
      "name": "密码输入框",
      "locators": [
        {
          "type": "resource-id",
          "value": "com.example.app:id/password",
          "priority": 1
        }
      ]
    }
  ]
}
```

## 支持的元素字段

### 基本字段
- `name` - 元素名称（必需）
- `description` - 元素描述（可选）
- `locators` - 定位符数组（必需）

### 定位符支持的快捷字段

如果不想使用 `locators` 数组，可以直接使用以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `resourceId` / `resource_id` | string | 资源ID，自动转为 resource-id 定位符 |
| `xpath` | string | XPath表达式 |
| `text` | string | 文本内容 |
| `id` | object | 包含xpath等子字段的对象 |

**示例**:
```json
{
  "name": "登录按钮",
  "resourceId": "com.example.app:id/login",
  "xpath": "//*[@text='登录']",
  "text": "登录"
}
```

自动转换为:
```json
{
  "name": "登录按钮",
  "locators": [
    {"type": "resource-id", "value": "com.example.app:id/login", "priority": 1},
    {"type": "xpath", "value": "//*[@text='登录']", "priority": 2},
    {"type": "text", "value": "登录", "priority": 3}
  ]
}
```

## YAML 格式支持

YAML 格式同样支持上述所有格式，只需将 JSON 改为 YAML 语法即可。

**示例**:
```yaml
version: "1.0"
screens:
  - name: "登录页面"
    elements:
      - name: "登录按钮"
        locators:
          - type: "text"
            value: "登录"
            priority: 1
```

## 错误处理

如果上传的文件格式不正确，系统会返回详细的错误信息：

```json
{
  "code": 4000,
  "message": "无法识别的数据格式。缺少必需的字段。可用字段: screens, pageInfo+elements, elements"
}
```

**解决方法**:
1. 检查文件格式是否符合上述任一格式
2. 确保至少包含一个必需的字段组合
3. 下载标准模板并按照格式填写

## 最佳实践

1. **使用标准格式**: 下载官方模板，按照标准格式填写
2. **提供多个定位符**: 为每个元素提供多个定位符，按优先级排序
3. **使用描述性名称**: 元素名称应清晰描述其用途
4. **添加描述信息**: 为复杂的元素添加描述字段
5. **验证导入结果**: 导入后检查元素列表，确保定位符正确

## 工具支持

使用 `xml_to_import_template.py` 工具可以从 uiautomator2 导出的 XML 自动生成标准格式的导入文件。

```bash
python xml_to_import_template.py dump.xml -n "登录页面" -o login.json
```
