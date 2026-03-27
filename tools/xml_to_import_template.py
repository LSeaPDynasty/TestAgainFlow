#!/usr/bin/env python3
"""
XML转导入模板工具

从uiautomator2导出的XML文件生成TestFlow导入模板
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET


def extract_element_attributes(node: ET.Element) -> Dict:
    """提取XML节点的属性"""
    attrs = {
        'text': node.attrib.get('text', ''),
        'resource-id': node.attrib.get('resource-id', ''),
        'class': node.attrib.get('class', ''),
        'package': node.attrib.get('package', ''),
        'content-desc': node.attrib.get('content-desc', ''),
        'clickable': node.attrib.get('clickable', 'false'),
        'checkable': node.attrib.get('checkable', 'false'),
        'enabled': node.attrib.get('enabled', 'true'),
        'focusable': node.attrib.get('focusable', 'false'),
        'bounds': node.attrib.get('bounds', ''),
    }
    return attrs


def is_interesting_element(attrs: Dict) -> bool:
    """判断是否是有意义的元素（值得导入）"""
    # 必须有resource-id或有意义的text
    has_id = bool(attrs['resource-id'])
    has_text = bool(attrs['text'] and len(attrs['text']) > 0 and not attrs['text'].startswith('com.'))
    has_content_desc = bool(attrs['content-desc'])

    # 可点击的元素更重要
    is_clickable = attrs['clickable'] == 'true'

    return (has_id or has_text or has_content_desc) and is_clickable


def generate_element_name(attrs: Dict) -> str:
    """生成元素名称"""
    # 优先使用text，其次resource-id，最后content-desc
    if attrs['text'] and len(attrs['text']) <= 20:
        return attrs['text']

    if attrs['content-desc']:
        return attrs['content-desc']

    if attrs['resource-id']:
        # 从resource-id中提取名称
        rid = attrs['resource-id']
        if ':' in rid:
            rid = rid.split(':')[-1]
        if '/' in rid:
            rid = rid.split('/')[-1]
        return rid.replace('_', ' ').title()

    return attrs['class'].split('.')[-1] if attrs['class'] else 'Unknown Element'


def generate_locators(attrs: Dict) -> List[Dict]:
    """生成定位符列表"""
    locators = []
    priority = 1

    # resource-id优先级最高
    if attrs['resource-id']:
        locators.append({
            'type': 'resource-id',
            'value': attrs['resource-id'],
            'priority': priority
        })
        priority += 1

    # text次之
    if attrs['text'] and attrs['text'].strip():
        locators.append({
            'type': 'text',
            'value': attrs['text'],
            'priority': priority
        })
        priority += 1

    # content-desc
    if attrs['content-desc'] and attrs['content-desc'].strip():
        locators.append({
            'type': 'content-desc',
            'value': attrs['content-desc'],
            'priority': priority
        })
        priority += 1

    # xpath作为备用
    if attrs['resource-id']:
        locators.append({
            'type': 'xpath',
            'value': f"//*[@resource-id='{attrs['resource-id']}']",
            'priority': priority
        })
    elif attrs['text']:
        locators.append({
            'type': 'xpath',
            'value': f"//*[@text='{attrs['text']}']",
            'priority': priority
        })

    return locators


def parse_xml_to_template(
    xml_file: Path,
    screen_name: str,
    activity: Optional[str] = None,
    min_elements: bool = False
) -> Dict:
    """解析XML文件生成导入模板"""

    tree = ET.parse(xml_file)
    root = tree.getroot()

    elements = []
    seen_elements = set()  # 用于去重

    def traverse_node(node: ET.Element, depth: int = 0):
        """递归遍历XML节点"""
        if depth > 20:  # 限制深度避免无限递归
            return

        attrs = extract_element_attributes(node)

        # 判断是否是感兴趣的元素
        if is_interesting_element(attrs):
            element_name = generate_element_name(attrs)
            element_key = f"{element_name}_{attrs['resource-id']}_{attrs['text']}"

            # 去重
            if element_key not in seen_elements:
                seen_elements.add(element_key)

                locators = generate_locators(attrs)
                if locators:  # 只有至少有一个定位符才添加
                    elements.append({
                        'name': element_name,
                        'description': f"Auto-imported from {xml_file.name}",
                        'locators': locators
                    })

        # 递归处理子节点
        for child in node:
            traverse_node(child, depth + 1)

    # 开始遍历
    traverse_node(root)

    # 如果启用min_elements，只保留前20个最重要的元素
    if min_elements and len(elements) > 20:
        elements = elements[:20]

    # 构建导入模板
    template = {
        'version': '1.0',
        'description': f'Auto-generated from {xml_file.name}',
        'screens': [
            {
                'name': screen_name,
                'activity': activity,
                'description': f'界面元素从 {xml_file.name} 自动导出',
                'elements': elements
            }
        ]
    }

    return template


def main():
    parser = argparse.ArgumentParser(
        description='从uiautomator2 XML文件生成TestFlow导入模板'
    )
    parser.add_argument(
        'xml_file',
        type=Path,
        help='uiautomator2导出的XML文件路径'
    )
    parser.add_argument(
        '-n', '--screen-name',
        required=True,
        help='界面名称'
    )
    parser.add_argument(
        '-a', '--activity',
        help='Activity名称'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='输出文件路径（默认为stdout）'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'yaml'],
        default='json',
        help='输出格式（默认json）'
    )
    parser.add_argument(
        '--min',
        action='store_true',
        help='只提取最重要的元素（最多20个）'
    )

    args = parser.parse_args()

    # 检查输入文件
    if not args.xml_file.exists():
        print(f"错误: 文件不存在: {args.xml_file}", file=sys.stderr)
        sys.exit(1)

    # 解析XML生成模板
    try:
        template = parse_xml_to_template(
            args.xml_file,
            args.screen_name,
            args.activity,
            args.min
        )
    except ET.ParseError as e:
        print(f"错误: XML解析失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 输出结果
    output = json.dumps(template, ensure_ascii=False, indent=2)

    if args.format == 'yaml':
        try:
            import yaml
            output = yaml.dump(template, allow_unicode=True, default_flow_style=False)
        except ImportError:
            print("错误: 需要安装PyYAML才能输出YAML格式", file=sys.stderr)
            sys.exit(1)

    if args.output:
        args.output.write_text(output, encoding='utf-8')
        print(f"✓ 模板已生成: {args.output}")
        print(f"  - 界面: {args.screen_name}")
        print(f"  - 元素数量: {len(template['screens'][0]['elements'])}")
    else:
        print(output)


if __name__ == '__main__':
    main()
