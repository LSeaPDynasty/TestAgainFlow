"""
Import router for bulk data import
"""
import json
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.bulk_import import BulkImportRequest, ElementsOnlyImportRequest, ImportResultSchema
from app.schemas.common import ApiResponse
from app.services.import_service import import_bulk_data, import_elements_to_screen
from app.utils.response import error, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])


def _parse_file_content(content: str, filename: str) -> Dict:
    """解析文件内容（JSON或YAML）"""
    try:
        # 尝试JSON
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 尝试YAML
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        logger.error("YAML库未安装，无法解析YAML文件")
        raise ValueError("YAML支持未安装，请使用JSON格式或安装PyYAML")
    except Exception as e:
        logger.error(f"YAML解析失败: {e}")
        raise ValueError(f"无法解析文件: {str(e)}")


@router.post("/bulk", response_model=ApiResponse[ImportResultSchema])
async def bulk_import(
    data: BulkImportRequest,
    db: Session = Depends(get_db_session),
):
    """批量导入界面和元素"""
    try:
        options = data.options or {}
        result = import_bulk_data(db, data, options)
        return ok(data=result, message=result.message)
    except Exception as e:
        logger.error(f"批量导入失败: {e}", exc_info=True)
        return error(code=5000, message=f"导入失败: {str(e)}")


@router.post("/elements")
async def import_elements(
    data: ElementsOnlyImportRequest,
    db: Session = Depends(get_db_session),
):
    """导入元素到指定界面"""
    try:
        options = data.options or {}
        result = import_elements_to_screen(db, data, options)
        return ok(data=result, message=result.message)
    except Exception as e:
        logger.error(f"元素导入失败: {e}", exc_info=True)
        return error(code=5000, message=f"导入失败: {str(e)}")


@router.post("/upload")
async def upload_import_file(
    file: UploadFile = File(...),
    skip_existing: bool = Form(True),
    create_screens: bool = Form(True),
    db: Session = Depends(get_db_session),
):
    """
    上传并导入文件（JSON或YAML）

    支持多种格式:
    - TestFlow标准格式 (screens字段)
    - pageInfo格式 (pageInfo + elements)
    - 纯元素列表格式 (elements数组)

    Args:
        file: 上传的文件
        skip_existing: 跳过已存在的界面/元素
        create_screens: 自动创建不存在的界面
        db: Database session
    """
    try:
        # 记录原始文件名用于调试
        logger.info(f"开始处理导入文件: {file.filename}")

        # 读取文件内容
        content = (await file.read()).decode("utf-8")
        logger.info(f"文件内容长度: {len(content)} 字符")

        # 解析文件
        try:
            parsed_data = _parse_file_content(content, file.filename)
            logger.info(f"解析后的数据类型: {type(parsed_data)}, 顶层键: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'N/A'}")
        except ValueError as e:
            logger.error(f"文件解析失败: {e}")
            return error(code=4000, message=str(e))

        # 转换为标准格式（如果不是标准格式）
        from app.services.import_converter import validate_and_convert

        try:
            converted_data, warnings = validate_and_convert(parsed_data)
            if warnings:
                logger.warning(f"数据转换警告: {warnings}")
            parsed_data = converted_data
        except Exception as e:
            # 转换失败，返回友好的错误信息
            logger.error(f"数据转换失败: {e}", exc_info=True)

            # 尝试提供更有用的错误信息
            if "pageInfo" in parsed_data:
                return error(
                    code=4000,
                    message=f"文件格式无法识别。pageInfo格式转换失败: {str(e)}。请下载标准模板或检查文件格式。"
                )
            elif "elements" in parsed_data:
                return error(
                    code=4000,
                    message=f"文件格式无法识别。elements字段格式错误: {str(e)}。请确保elements是数组且每个元素有name和定位符信息。"
                )
            else:
                return error(
                    code=4000,
                    message=f"文件格式无法识别。缺少必需的字段(screens、pageInfo+elements或elements)。请下载标准模板: {str(e)}"
                )

        # 检查版本
        version = parsed_data.get("version")
        if version and version != "1.0":
            logger.warning(f"不支持的模板版本: {version}")

        # 判断导入类型
        if "target_screen" in parsed_data:
            # 元素导入模式
            import_data = ElementsOnlyImportRequest(
                target_screen=parsed_data["target_screen"],
                elements=parsed_data.get("elements", []),
                options=parsed_data.get("options", {}),
            )
            options = {"skip_existing": skip_existing}
            result = import_elements_to_screen(db, import_data, options)
        else:
            # 批量导入模式
            import_data = BulkImportRequest(**parsed_data)
            options = {
                "skip_existing": skip_existing,
                "create_screens": create_screens,
            }
            result = import_bulk_data(db, import_data, options)

        if result.success:
            return ok(data=result, message=result.message)
        else:
            return error(code=4000, message=result.message, data=result)

    except Exception as e:
        logger.error(f"文件导入失败: {e}", exc_info=True)
        return error(code=5000, message=f"导入失败: {str(e)}")


@router.post("/preview")
async def preview_import_file(
    file: UploadFile = File(...),
):
    """
    预览导入文件转换结果，不实际导入

    用于调试文件格式问题
    """
    try:
        logger.info(f"预览导入文件: {file.filename}")

        # 读取文件内容
        content = (await file.read()).decode("utf-8")

        # 解析文件
        try:
            parsed_data = _parse_file_content(content, file.filename)
        except ValueError as e:
            return {
                "success": False,
                "error": f"文件解析失败: {str(e)}",
                "original_format": "unknown"
            }

        # 转换为标准格式
        from app.services.import_converter import validate_and_convert

        try:
            converted_data, warnings = validate_and_convert(parsed_data)
            return {
                "success": True,
                "warnings": warnings,
                "converted_data": converted_data,
                "screens_count": len(converted_data.get("screens", [])),
                "total_elements": sum(len(screen.get("elements", [])) for screen in converted_data.get("screens", []))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_data_keys": list(parsed_data.keys()) if isinstance(parsed_data, dict) else str(type(parsed_data)),
                "hint": "请检查文件格式是否符合支持格式之一"
            }

    except Exception as e:
        logger.error(f"文件预览失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/template/json")
async def get_json_template():
    """获取JSON导入模板"""
    from pathlib import Path
    from fastapi.responses import Response

    # 支持从多个位置查找模板文件
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent / "templates" / "import_template.json",
        Path(__file__).parent.parent.parent.parent / "templates" / "import_template.json",
        Path(__file__).parent.parent.parent / "templates" / "import_template.json",
    ]

    template_path = None
    for path in possible_paths:
        if path.exists():
            template_path = path
            break

    if not template_path:
        return error(code=404, message="模板文件不存在")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="import_template.json"'},
    )


@router.get("/template/yaml")
async def get_yaml_template():
    """获取YAML导入模板"""
    from pathlib import Path
    from fastapi.responses import Response

    # 支持从多个位置查找模板文件
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent / "templates" / "import_template.yaml",
        Path(__file__).parent.parent.parent.parent / "templates" / "import_template.yaml",
        Path(__file__).parent.parent.parent / "templates" / "import_template.yaml",
    ]

    template_path = None
    for path in possible_paths:
        if path.exists():
            template_path = path
            break

    if not template_path:
        return error(code=404, message="模板文件不存在")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="text/yaml",
        headers={"Content-Disposition": 'attachment; filename="import_template.yaml"'},
    )


@router.get("/template/elements-only")
async def get_elements_only_template():
    """获取元素导入模板"""
    from pathlib import Path
    from fastapi.responses import Response

    # 支持从多个位置查找模板文件
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent / "templates" / "elements_only_template.json",
        Path(__file__).parent.parent.parent.parent / "templates" / "elements_only_template.json",
        Path(__file__).parent.parent.parent / "templates" / "elements_only_template.json",
    ]

    template_path = None
    for path in possible_paths:
        if path.exists():
            template_path = path
            break

    if not template_path:
        return error(code=404, message="模板文件不存在")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="elements_only_template.json"'},
    )
