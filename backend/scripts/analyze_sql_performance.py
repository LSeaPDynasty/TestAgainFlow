# -*- coding: utf-8 -*-
"""
SQL性能分析脚本
检查所有repository的SQL查询问题
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any


class SQLAnalyzer:
    """SQL查询分析器"""

    def __init__(self, repo_dir: str):
        self.repo_dir = Path(repo_dir)
        self.issues = []

    def analyze_all(self) -> Dict[str, Any]:
        """分析所有repository文件"""
        results = {
            "total_files": 0,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }

        # 查找所有repository文件
        repo_files = list(self.repo_dir.glob("*_repo.py"))
        results["total_files"] = len(repo_files)

        for file_path in repo_files:
            self._analyze_file(file_path, results)

        return results

    def _analyze_file(self, file_path: Path, results: Dict):
        """分析单个文件"""
        content = file_path.read_text(encoding='utf-8')
        filename = file_path.name

        # 检查问题模式
        self._check_n_plus_1(content, filename, results)
        self._check_loop_queries(content, filename, results)
        self._check_missing_joinedload(content, filename, results)
        self._check_select_star(content, filename, results)
        self._check_missing_indexes(content, filename, results)

    def _check_n_plus_1(self, content: str, filename: str, results: Dict):
        """检查N+1查询问题"""
        # 模式：在循环中调用get_with_方法
        pattern = r'for\s+\w+\s+in\s+.*:.*?get_with_\w+\('

        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            line_start = content[:match.start()].count('\n') + 1
            results["issues"].append({
                "file": filename,
                "line": line_start,
                "type": "N+1查询",
                "severity": "HIGH",
                "pattern": "循环中调用get_with_*方法"
            })

    def _check_loop_queries(self, content: str, filename: str, results: Dict):
        """检查循环中的数据库查询"""
        # 模式：for循环中有db.execute/db.query
        pattern = r'for\s+\w+\s+in\s+.*?:.*?(?:db\.execute|db\.query|self\.db\.execute|self\.db\.query)'

        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            line_start = content[:match.start()].count('\n') + 1
            results["issues"].append({
                "file": filename,
                "line": line_start,
                "type": "循环查询",
                "severity": "HIGH",
                "pattern": "for循环中有数据库查询"
            })

    def _check_missing_joinedload(self, content: str, filename: str, results: Dict):
        """检查是否缺少joinedload"""
        # 模式：查询Entity但没有joinedload关联
        has_relationship = 'relationship' in content or 'joinedload' in content

        if has_relationship:
            # 检查是否有select但没有options(joinedload(...))
            has_select = 'select(' in content
            has_joinedload = 'joinedload(' in content

            if has_select and not has_joinedload:
                results["warnings"].append({
                    "file": filename,
                    "type": "缺少joinedload",
                    "severity": "MEDIUM",
                    "message": "有relationship但没使用joinedload"
                })

    def _check_select_star(self, content: str, filename: str, results: Dict):
        """检查SELECT *查询"""
        pattern = r'SELECT\s+\*\s+FROM'

        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_start = content[:match.start()].count('\n') + 1
            results["warnings"].append({
                "file": filename,
                "line": line_start,
                "type": "SELECT *",
                "severity": "LOW",
                "message": "使用SELECT *可能影响性能"
            })

    def _check_missing_indexes(self, content: str, filename: str, results: Dict):
        """检查可能的缺失索引"""
        # 模式：filter中使用常见字段但可能没有索引
        common_filter_fields = ['name', 'created_at', 'status', 'type']

        for field in common_filter_fields:
            # 检查是否有filter但可能缺少索引
            if f'filter({field}' in content or f'where.*{field}' in content.lower():
                results["recommendations"].append({
                    "file": filename,
                    "field": field,
                    "message": f"确保{field}字段有索引"
                })


def print_results(results: Dict):
    """打印分析结果"""
    print("=" * 80)
    print("SQL Performance Analysis Report")
    print("=" * 80)

    print(f"\n[FILES] Scanned: {results['total_files']}")
    print(f"[ISSUES] High Severity: {len(results['issues'])}")
    print(f"[WARNINGS] Medium/Low: {len(results['warnings'])}")
    print(f"[RECOMMENDATIONS] Total: {len(results['recommendations'])}")

    if results['issues']:
        print("\n" + "=" * 80)
        print("[HIGH SEVERITY] Issues")
        print("=" * 80)
        for idx, issue in enumerate(results['issues'], 1):
            print(f"\n{idx}. {issue['file']}:{issue.get('line', '?')}")
            print(f"   Type: {issue['type']}")
            print(f"   Pattern: {issue['pattern']}")

    if results['warnings']:
        print("\n" + "=" * 80)
        print("[WARNINGS] Medium/Low Severity")
        print("=" * 80)
        for idx, warning in enumerate(results['warnings'], 1):
            print(f"\n{idx}. {warning['file']}")
            print(f"   Type: {warning['type']}")
            print(f"   Message: {warning['message']}")

    if results['recommendations']:
        print("\n" + "=" * 80)
        print("[RECOMMENDATIONS] Optimization Suggestions")
        print("=" * 80)
        for idx, rec in enumerate(results['recommendations'], 1):
            print(f"\n{idx}. {rec['file']}")
            print(f"   Field: {rec.get('field', '')}")
            print(f"   Suggestion: {rec['message']}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    analyzer = SQLAnalyzer("app/repositories")
    results = analyzer.analyze_all()
    print_results(results)
