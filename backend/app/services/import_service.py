"""
Import service for bulk data import
"""
import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.repositories.screen_repo import ScreenRepository
from app.repositories.element_repo import ElementRepository
from app.schemas.bulk_import import (
    BulkImportRequest,
    ElementsOnlyImportRequest,
    ImportResultSchema,
    ElementImportSchema,
    ScreenImportSchema,
)
from app.schemas.element import ElementCreate
from app.schemas.screen import ScreenCreate

logger = logging.getLogger(__name__)


class ImportError(Exception):
    """Import error"""
    pass


def import_bulk_data(
    db: Session, data: BulkImportRequest, options: Optional[Dict] = None
) -> ImportResultSchema:
    """
    批量导入界面和元素

    Args:
        db: Database session
        data: Import data
        options: Import options (skip_existing, create_screens, etc.)

    Returns:
        ImportResultSchema: Import result
    """
    options = options or {}
    skip_existing = options.get("skip_existing", True)  # 跳过已存在的界面/元素
    create_screens = options.get("create_screens", True)  # 自动创建界面

    created_screens = 0
    created_elements = 0
    skipped_screens = []
    skipped_elements = []
    errors = []

    screen_repo = ScreenRepository(db)
    element_repo = ElementRepository(db)

    try:
        for screen_data in data.screens:
            try:
                # 检查界面是否已存在
                existing_screen = screen_repo.get_by_name(screen_data.name)

                screen_id = None
                if existing_screen:
                    if skip_existing:
                        skipped_screens.append(screen_data.name)
                        # 如果界面已存在且跳过，仍然可以尝试导入元素
                        screen_id = existing_screen.id
                    else:
                        errors.append(f"界面 '{screen_data.name}' 已存在")
                        continue
                else:
                    if create_screens:
                        # 创建新界面
                        screen_create = ScreenCreate(
                            name=screen_data.name,
                            activity=screen_data.activity,
                            description=screen_data.description,
                        )
                        new_screen = screen_repo.create(screen_create.model_dump())
                        screen_id = new_screen.id
                        created_screens += 1
                        logger.info(f"✓ 创建界面: {screen_data.name}")
                    else:
                        errors.append(f"界面 '{screen_data.name}' 不存在且未启用自动创建")
                        continue

                # 导入元素
                if screen_id and screen_data.elements:
                    for element_data in screen_data.elements:
                        try:
                            # 检查元素是否已存在（在同一界面下）
                            existing_elements = element_repo.list_by_screen(screen_id)
                            element_exists = any(
                                e.name == element_data.name for e in existing_elements
                            )

                            if element_exists and skip_existing:
                                skipped_elements.append(f"{screen_data.name}/{element_data.name}")
                                continue

                            # 创建元素
                            element_create = ElementCreate(
                                name=element_data.name,
                                description=element_data.description,
                                screen_id=screen_id,
                                locators=[loc.model_dump() for loc in element_data.locators],
                            )
                            logger.info(f"准备创建元素: {element_data.name}, 描述: {element_data.description}")
                            element_repo.create_with_locators(element_create.model_dump())
                            created_elements += 1
                            logger.info(f"  ✓ 创建元素: {element_data.name}")

                        except Exception as e:
                            error_msg = f"元素 '{element_data.name}' 导入失败: {str(e)}"
                            errors.append(error_msg)
                            logger.error(error_msg)

            except Exception as e:
                error_msg = f"界面 '{screen_data.name}' 导入失败: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # 判断整体是否成功
        success = len(errors) == 0 or (created_screens > 0 or created_elements > 0)
        message = f"导入完成: 创建 {created_screens} 个界面, {created_elements} 个元素"
        if skipped_screens:
            message += f", 跳过 {len(skipped_screens)} 个已存在界面"
        if skipped_elements:
            message += f", 跳过 {len(skipped_elements)} 个已存在元素"
        if errors:
            message += f", {len(errors)} 个错误"

        return ImportResultSchema(
            success=success,
            message=message,
            created_screens=created_screens,
            created_elements=created_elements,
            skipped_screens=skipped_screens,
            skipped_elements=skipped_elements,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"批量导入失败: {e}", exc_info=True)
        return ImportResultSchema(
            success=False,
            message=f"导入失败: {str(e)}",
            created_screens=created_screens,
            created_elements=created_elements,
            skipped_screens=skipped_screens,
            skipped_elements=skipped_elements,
            errors=errors + [str(e)],
        )


def import_elements_to_screen(
    db: Session, data: ElementsOnlyImportRequest, options: Optional[Dict] = None
) -> ImportResultSchema:
    """
    导入元素到已存在的界面

    Args:
        db: Database session
        data: Elements import data
        options: Import options

    Returns:
        ImportResultSchema: Import result
    """
    options = options or {}
    skip_existing = options.get("skip_existing", True)

    created_elements = 0
    skipped_elements = []
    errors = []

    screen_repo = ScreenRepository(db)
    element_repo = ElementRepository(db)

    try:
        # 查找目标界面
        target_screen = screen_repo.get_by_name(data.target_screen)
        if not target_screen:
            return ImportResultSchema(
                success=False,
                message=f"界面 '{data.target_screen}' 不存在",
                created_elements=0,
                skipped_elements=[],
                errors=[f"界面 '{data.target_screen}' 不存在，请先创建该界面"],
            )

        # 导入元素
        for element_data in data.elements:
            try:
                # 检查元素是否已存在
                existing_elements = element_repo.list_by_screen(target_screen.id)
                element_exists = any(e.name == element_data.name for e in existing_elements)

                if element_exists and skip_existing:
                    skipped_elements.append(element_data.name)
                    continue

                # 创建元素
                element_create = ElementCreate(
                    name=element_data.name,
                    description=element_data.description,
                    screen_id=target_screen.id,
                    locators=[loc.model_dump() for loc in element_data.locators],
                )
                element_repo.create_with_locators(element_create.model_dump())
                created_elements += 1
                logger.info(f"✓ 创建元素: {element_data.name}")

            except Exception as e:
                error_msg = f"元素 '{element_data.name}' 导入失败: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # 判断整体是否成功
        success = len(errors) == 0 or created_elements > 0
        message = f"导入完成: 创建 {created_elements} 个元素"
        if skipped_elements:
            message += f", 跳过 {len(skipped_elements)} 个已存在元素"
        if errors:
            message += f", {len(errors)} 个错误"

        return ImportResultSchema(
            success=success,
            message=message,
            created_screens=0,
            created_elements=created_elements,
            skipped_screens=[],
            skipped_elements=skipped_elements,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"元素导入失败: {e}", exc_info=True)
        return ImportResultSchema(
            success=False,
            message=f"导入失败: {str(e)}",
            created_elements=created_elements,
            skipped_elements=skipped_elements,
            errors=errors + [str(e)],
        )
