"""
Project repository - 项目数据访问层
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.project import Project, ProjectStatus, ProjectPriority
from app.utils.pagination import calculate_offset


class ProjectRepository:
    """项目数据访问对象"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: Dict[str, Any]) -> Project:
        """创建项目"""
        # 处理标签列表转换为字符串
        if "tags" in data and isinstance(data["tags"], list):
            data["tags"] = ",".join(data["tags"])

        project = Project(**data)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get(self, project_id: int) -> Optional[Project]:
        """根据ID获取项目"""
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_by_name(self, name: str) -> Optional[Project]:
        """根据名称获取项目"""
        return self.db.query(Project).filter(Project.name == name).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Project], int]:
        """
        获取项目列表

        Args:
            skip: 跳过记录数
            limit: 返回记录数
            status: 状态筛选
            priority: 优先级筛选
            search: 搜索关键词

        Returns:
            (项目列表, 总数)
        """
        query = self.db.query(Project)

        # 状态筛选
        if status:
            query = query.filter(Project.status == status)

        # 优先级筛选
        if priority:
            query = query.filter(Project.priority == priority)

        # 搜索
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Project.name.like(search_pattern),
                    Project.description.like(search_pattern),
                )
            )

        # 总数
        total = query.count()

        # 分页和排序
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

        return projects, total

    def update(self, project: Project, data: Dict[str, Any]) -> Project:
        """更新项目"""
        # 处理标签列表转换为字符串
        if "tags" in data and isinstance(data["tags"], list):
            data["tags"] = ",".join(data["tags"])

        for key, value in data.items():
            if hasattr(project, key):
                setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        """删除项目"""
        self.db.delete(project)
        self.db.commit()

    def get_statistics(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目统计信息

        Args:
            project_id: 项目ID

        Returns:
            统计信息字典
        """
        from app.models.testcase import Testcase
        from app.models.suite import Suite
        from app.models.run_history import RunHistory

        # 用例数量
        testcase_count = self.db.query(func.count(Testcase.id)).filter(
            Testcase.project_id == project_id
        ).scalar() or 0

        # 套件数量
        suite_count = self.db.query(func.count(Suite.id)).filter(
            Suite.project_id == project_id
        ).scalar() or 0

        # 执行次数
        run_count = self.db.query(func.count(RunHistory.id)).filter(
            RunHistory.project_id == project_id
        ).scalar() or 0

        # 通过的执行次数
        pass_count = self.db.query(func.count(RunHistory.id)).filter(
            and_(
                RunHistory.project_id == project_id,
                RunHistory.result == "pass"
            )
        ).scalar() or 0

        # 通过率
        pass_rate = (pass_count / run_count * 100) if run_count > 0 else 0

        return {
            "testcase_count": testcase_count,
            "suite_count": suite_count,
            "run_count": run_count,
            "pass_count": pass_count,
            "pass_rate": round(pass_rate, 2),
        }
