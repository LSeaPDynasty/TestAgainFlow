# TestFlow 导入工具使用指南

## XML转导入模板工具

`xml_to_import_template.py` 可以将 uiautomator2 导出的 XML 文件转换为 TestFlow 导入模板。

### 安装依赖

```bash
pip install pyyaml
```

### 基本用法

```bash
# 从XML文件生成JSON模板
python xml_to_import_template.py uiautomator_dump.xml -n "登录页面" -o login_template.json

# 生成YAML格式
python xml_to_import_template.py uiautomator_dump.xml -n "登录页面" --format yaml -o login_template.yaml

# 指定Activity名称
python xml_to_import_template.py uiautomator_dump.xml -n "登录页面" -a "com.example.app.MainActivity" -o login_template.json

# 只提取最重要的元素（最多20个）
python xml_to_import_template.py uiautomator_dump.xml -n "登录页面" --min -o login_template.json

# 输出到stdout
python xml_to_import_template.py uiautomator_dump.xml -n "登录页面"
```

### 获取 uiautomator2 XML dump

```python
import uiautomator2 as u2

# 连接设备
d = u2.connect('device_serial')

# 导出XML
xml = d.dump_hierarchy()

# 保存到文件
with open('uiautomator_dump.xml', 'w', encoding='utf-8') as f:
    f.write(xml)
```

或通过命令行：

```bash
# 使用adb
adb shell uiautomator dump /sdcard/ui.xml
adb pull /sdcard/ui.xml uiautomator_dump.xml

# 使用uiautomator2
python -c "import uiautomator2 as u2; d = u2.connect(); print(d.dump_hierarchy())" > dump.xml
```

### 完整工作流程

```bash
# 1. 连接设备并导出XML
adb shell uiautomator dump /sdcard/ui.xml
adb pull /sdcard/ui.xml current_screen.xml

# 2. 生成导入模板
python xml_to_import_template.py current_screen.xml \
  -n "当前页面" \
  -a "com.example.app.CurrentActivity" \
  -o import_template.json

# 3. （可选）编辑模板，调整元素名称和定位符

# 4. 通过API或前端界面导入
curl -X POST http://localhost:8000/api/v1/import/upload \
  -F "file=@import_template.json" \
  -F "skip_existing=true" \
  -F "create_screens=true"
```

### 元素选择逻辑

工具会自动筛选值得导入的元素：

- ✅ 有 `resource-id` 的元素
- ✅ 有有意义文本（text）的元素
- ✅ 有 `content-desc` 的元素
- ✅ 可点击（clickable=true）的元素优先
- ❌ 纯布局元素（如LinearLayout、FrameLayout）
- ❌ 空文本或包含包名的文本

### 定位符生成规则

工具按以下优先级生成定位符：

1. **resource-id** (priority: 1) - 最稳定
2. **text** (priority: 2) - 文本内容
3. **content-desc** (priority: 3) - 描述信息
4. **xpath** (priority: 4) - 作为备用

### 示例输出

输入 XML:
```xml
<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy>
  <node resource-id="com.example.app:id/login_button" text="登录" clickable="true" class="android.widget.Button" />
</hierarchy>
```

输出 JSON:
```json
{
  "version": "1.0",
  "description": "Auto-generated from input.xml",
  "screens": [
    {
      "name": "登录页面",
      "activity": null,
      "description": "界面元素从 input.xml 自动导出",
      "elements": [
        {
          "name": "登录",
          "description": "Auto-imported from input.xml",
          "locators": [
            {
              "type": "resource-id",
              "value": "com.example.app:id/login_button",
              "priority": 1
            },
            {
              "type": "text",
              "value": "登录",
              "priority": 2
            },
            {
              "type": "xpath",
              "value": "//*[@resource-id='com.example.app:id/login_button']",
              "priority": 3
            }
          ]
        }
      ]
    }
  ]
}
```

## 批量处理脚本

处理多个XML文件：

```bash
#!/bin/bash
# batch_import.sh

for xml_file in screens/*.xml; do
  screen_name=$(basename "$xml_file" .xml)
  output_file="templates/${screen_name}.json"

  python xml_to_import_template.py "$xml_file" \
    -n "$screen_name" \
    -o "$output_file"

  echo "✓ Generated: $output_file"
done
```

## 故障排除

### 问题1: XML解析失败

**原因**: XML文件格式不正确或损坏

**解决**: 重新导出XML文件
```bash
adb shell uiautomator dump /sdcard/ui.xml --compressed
adb pull /sdcard/ui.xml
```

### 问题2: 导出的元素太多

**原因**: 界面复杂，包含了太多布局元素

**解决**: 使用 `--min` 参数只提取重要元素
```bash
python xml_to_import_template.py input.xml -n "页面" --min -o output.json
```

### 问题3: 元素名称重复

**原因**: 多个元素有相同的text或resource-id

**解决**: 手动编辑生成的模板，为元素添加唯一名称

### 问题4: 定位符不准确

**原因**: 自动生成的定位符可能不够精确

**解决**:
1. 编辑模板，调整定位符优先级
2. 添加更多备用定位符
3. 使用更具体的xpath表达式

## 高级用法

### 自定义元素筛选

编辑 `xml_to_import_template.py` 中的 `is_interesting_element` 函数来自定义筛选逻辑。

```python
def is_interesting_element(attrs: Dict) -> bool:
    # 只导入特定类型的元素
    if 'Button' not in attrs['class']:
        return False

    # 必须有resource-id
    if not attrs['resource-id']:
        return False

    return True
```

### 自定义元素命名

编辑 `generate_element_name` 函数来自定义元素命名规则。

```python
def generate_element_name(attrs: Dict) -> str:
    # 使用resource-id的最后一部分作为名称
    if attrs['resource-id']:
        rid = attrs['resource-id']
        return rid.split('/')[-1].replace('_', ' ').title()

    # 默认逻辑
    return attrs['text'] or 'Unknown Element'
```
