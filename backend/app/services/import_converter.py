"""
Import data converter - converts various formats to TestFlow import format
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def convert_to_import_format(data: Dict) -> Dict:
    """
    转换各种格式的数据为TestFlow导入格式

    支持的格式:
    1. TestFlow标准格式 (包含screens字段)
    2. pageInfo格式 (包含pageInfo和elements字段)
    3. 纯元素列表格式 (只包含elements数组)
    """
    # 已经是标准格式
    if "screens" in data:
        return data

    # pageInfo格式转换
    if "pageInfo" in data and "elements" in data:
        return convert_pageinfo_format(data)

    # 纯元素列表格式
    if "elements" in data and isinstance(data["elements"], list):
        return {
            "version": "1.0",
            "screens": [
                {
                    "name": data.get("screenName", "导入的界面"),
                    "description": data.get("description", "从外部文件导入"),
                    "elements": data["elements"]
                }
            ]
        }

    # 单个元素对象
    if "name" in data and "locators" in data:
        return {
            "version": "1.0",
            "screens": [
                {
                    "name": data.get("screenName", "导入的界面"),
                    "description": "从外部文件导入",
                    "elements": [data]
                }
            ]
        }

    raise ValueError(f"无法识别的数据格式。缺少必需的字段。可用字段: screens, pageInfo+elements, elements")


def convert_pageinfo_format(data: Dict) -> Dict:
    """
    转换pageInfo格式为TestFlow格式

    输入示例:
    {
        "pageInfo": {"pageName": "登录页面"},
        "elements": [...] 或 {"elementName": {...}, ...}
    }
    """
    # 确保 data 是字典
    if not isinstance(data, dict):
        raise ValueError(f"数据格式错误，期望字典，实际得到: {type(data)}")

    page_info = data.get("pageInfo", {})
    if not isinstance(page_info, dict):
        page_info = {}

    elements_input = data.get("elements", [])

    # 处理 elements 是对象（字典）而不是数组的情况
    # 例如: {"elements": {"button1": {"type": "xpath", "value": "..."}, ...}}
    if isinstance(elements_input, dict):
        logger.info(f"检测到elements是对象格式，包含 {len(elements_input)} 个元素定义")
        elements_list = []
        for elem_name, elem_data in elements_input.items():
            if isinstance(elem_data, dict):
                # 将元素名称和定位符合并
                combined_elem = {
                    "name": elem_name,
                    **elem_data
                }
                elements_list.append(combined_elem)
            else:
                logger.warning(f"跳过无效元素 {elem_name}: {type(elem_data)}")
        elements = elements_list
    elif isinstance(elements_input, list):
        elements = elements_input
    else:
        logger.warning(f"elements 字段类型错误: {type(elements_input)}，使用空数组")
        elements = []

    screen_name = page_info.get("pageName") or page_info.get("name") or "导入的界面"

    converted_elements = []
    for i, elem in enumerate(elements):
        try:
            converted_elem = convert_element(elem)
            if converted_elem:
                converted_elements.append(converted_elem)
        except Exception as e:
            logger.warning(f"转换第 {i+1} 个元素时出错: {e}, 跳过该元素")
            continue

    # 如果没有有效元素，创建一个空数组而不是报错
    if not converted_elements:
        logger.warning("没有找到有效的元素，将创建空界面的导入")

    return {
        "version": "1.0",
        "screens": [
            {
                "name": screen_name,
                "activity": page_info.get("activity"),
                "description": page_info.get("description", f"从 {page_info.get('pageName', '外部文件')} 导入"),
                "elements": converted_elements
            }
        ]
    }


def convert_element(elem: Any) -> Optional[Dict]:
    """
    转换单个元素

    支持多种定位符字段格式:
    1. 标准locators数组
    2. type + value 格式
    3. 分散的定位符字段 (resourceId, xpath, text等)
    """
    # 如果 elem 是字符串或其他非字典类型，跳过
    if not elem or not isinstance(elem, dict):
        logger.warning(f"跳过无效元素（类型错误）: {type(elem)} = {elem}")
        return None

    # 提取基本信息
    name = elem.get("name") or elem.get("elementName") or elem.get("element_name") or "未命名元素"
    description = elem.get("description", "")

    logger.info(f"正在转换元素: {name}, 描述: {description}, 原始字段: {list(elem.keys())}")

    # 提取定位符
    locators = []

    # 方法1: 标准locators数组
    if "locators" in elem and isinstance(elem["locators"], list):
        locators = elem["locators"]
        logger.info(f"  -> 使用标准locators数组，数量: {len(locators)}")

    # 方法2: type + value 格式 (如: {"type": "xpath", "value": "..."})
    elif "type" in elem and "value" in elem:
        locator_type = elem["type"]
        locator_value = elem["value"]

        # 映射type到标准类型
        type_mapping = {
            "id": "resource-id",
            "resourceId": "resource-id",
            "resource-id": "resource-id",
            "xpath": "xpath",
            "text": "text",
            "content-desc": "content-desc",
            "contentDescription": "content-desc",
            "class": "class",
            "className": "class",
        }

        standard_type = type_mapping.get(locator_type, locator_type)

        locators = [{
            "type": standard_type,
            "value": locator_value,
            "priority": 1
        }]
        logger.info(f"  -> 使用type+value格式: {standard_type} = {locator_value}")

    # 方法3: 单个locator字段
    elif "locator" in elem:
        locator = elem["locator"]
        if isinstance(locator, dict):
            locators = [locator]
            logger.info(f"  -> 使用单个locator字段")
        elif isinstance(locator, str):
            # 尝试自动识别定位符类型
            locators = _guess_locator_type(locator)
            logger.info(f"  -> 从字符串识别定位符: {locator}")

    # 方法4: 分散的定位符字段 (resourceId, xpath, text等)
    else:
        logger.info(f"  -> 尝试从分散字段提取定位符")
        locator_list = []

        # resource-id
        if "resourceId" in elem or "resource_id" in elem:
            rid = elem.get("resourceId") or elem.get("resource_id")
            if rid and isinstance(rid, str):
                locator_list.append({
                    "type": "resource-id",
                    "value": rid,
                    "priority": 1
                })
                logger.info(f"    -> 找到resource-id: {rid}")

        # xpath
        if "xpath" in elem:
            xpath = elem["xpath"]
            if xpath and isinstance(xpath, str):
                locator_list.append({
                    "type": "xpath",
                    "value": xpath,
                    "priority": len(locator_list) + 1 if locator_list else 2
                })
                logger.info(f"    -> 找到xpath: {xpath}")
            elif xpath:
                logger.warning(f"    -> xpath字段值类型错误: {type(xpath)} = {xpath}")

        # text
        if "text" in elem:
            text = elem["text"]
            if text and isinstance(text, str):
                locator_list.append({
                    "type": "text",
                    "value": text,
                    "priority": len(locator_list) + 1 if locator_list else 2
                })
                logger.info(f"    -> 找到text: {text}")

        # id 字段（可能是数字或字典）
        if "id" in elem:
            elem_id = elem["id"]
            if isinstance(elem_id, dict) and "xpath" in elem_id:
                xpath = elem_id["xpath"]
                if xpath and isinstance(xpath, str):
                    locator_list.append({
                        "type": "xpath",
                        "value": xpath,
                        "priority": len(locator_list) + 1 if locator_list else 2
                    })
                    logger.info(f"    -> 从id.xpath找到xpath: {xpath}")

        locators = locator_list

    # 如果没有定位符，尝试从其他字段提取
    if not locators:
        logger.warning(f"元素 {name} 没有定位符，跳过。可用字段: {list(elem.keys())}")
        return None

    logger.info(f"  -> 成功转换元素 {name}，定位符数量: {len(locators)}")
    return {
        "name": name,
        "description": description,
        "locators": locators
    }


def _guess_locator_type(value: str) -> List[Dict]:
    """
    根据字符串猜测定位符类型

    例如:
    - "com.app:id/button" -> resource-id
    - "//*[@text='登录']" -> xpath
    - "登录" -> text
    """
    locators = []

    # 检查是否是 resource-id (包含:id/)
    if ":id/" in value or (value.startswith("com.") and ":id/" in value):
        locators.append({
            "type": "resource-id",
            "value": value,
            "priority": 1
        })

    # 检查是否是 xpath (包含 // 或 /*)
    if "//" in value or value.startswith("/"):
        locators.append({
            "type": "xpath",
            "value": value,
            "priority": 1
        })

    # 默认作为 text
    if not locators:
        locators.append({
            "type": "text",
            "value": value,
            "priority": 1
        })

    return locators


def validate_and_convert(data: Dict) -> tuple[Dict, List[str]]:
    """
    验证并转换数据

    返回: (转换后的数据, 警告信息列表)
    """
    warnings = []

    try:
        converted = convert_to_import_format(data)
        return converted, warnings
    except ValueError as e:
        # 尝试修复或提供更多信息
        if "pageInfo" in data:
            warnings.append("检测到pageInfo格式但转换失败")
            # 尝试最基本的转换
            try:
                return convert_pageinfo_format(data), warnings
            except Exception as e2:
                raise ValueError(f"无法转换pageInfo格式: {str(e2)}")

        raise e
