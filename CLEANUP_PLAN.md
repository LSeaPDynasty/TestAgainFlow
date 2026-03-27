# TestFlow 项目清理计划

## 清理日期
2026-03-24

## 待删除文件列表

### 根目录临时文件
- `test_executor_websocket.py` - WebSocket测试脚本
- `test_executor_ws_simple.py` - WebSocket测试脚本
- `test_websocket.py` - WebSocket测试脚本
- `create_device.json` - 测试数据
- `.pytest_cache/` - 生成的缓存目录

### Backend临时文件
- `backend/test_ai_config.py` - AI配置临时测试
- `backend/test_api_detailed.py` - API临时测试
- `backend/test_models.py` - 模型临时测试
- `backend/IMPLEMENTATION_REPORT.md` - 旧实现报告（已有更新的AI_INTEGRATION_IMPLEMENTATION_SUMMARY.md）
- `backend/.coverage` - 覆盖率报告（生成文件）
- `backend/htmlcov/` - 覆盖率HTML目录（生成文件）
- `backend/test.db` - 临时测试数据库
- `backend/.pytest_cache/` - 生成的缓存目录

## 保留文件说明

### 核心文档
- `README.md` - 主文档
- `AI_INTEGRATION_IMPLEMENTATION_SUMMARY.md` - AI集成最新实现总结
- `EXECUTION_GUIDE.md` - 执行器使用指南
- `EXECUTOR_INTEGRATION.md` - 执行器集成文档
- `RECOVERY_GUIDE.md` - 恢复指南
- `backend/README.md` - 后端文档

### 实用脚本
- `check_db.py` - 数据库检查工具
- `start-all.bat/sh` - 启动脚本
- `backend/run.py` - 应用入口
- `kill_port_8000.bat` / `run_port_8001.bat` - 端口管理工具

### 模板文件
- `templates/import_template.json` - JSON导入模板
- `templates/import_template.yaml` - YAML导入模板
- `templates/elements_only_template.json` - 元素模板
- `templates/testcase_recursive_import_template.json` - 递归导入模板
- `templates/README.md` - 模板使用说明
- `templates/SUPPORTED_FORMATS.md` - 支持格式说明

## .gitignore 建议添加

```
# 测试和覆盖率报告
.coverage
htmlcov/
.pytest_cache/
**/.pytest_cache/

# 临时数据库
*.db
test.db
testflow.db

# 临时测试脚本
test_*.py
check_*.py

# 临时JSON数据
create_device.json
*_test.json

# 环境变量
.env
.env.local
```

## 清理后项目结构

```
testflow/
├── README.md                           # 主文档
├── AI_INTEGRATION_IMPLEMENTATION_SUMMARY.md  # AI集成总结
├── EXECUTION_GUIDE.md                  # 执行指南
├── EXECUTOR_INTEGRATION.md             # 执行器集成
├── RECOVERY_GUIDE.md                   # 恢复指南
├── start-all.bat                       # Windows启动脚本
├── start-all.sh                        # Linux启动脚本
├── backend/
│   ├── README.md
│   ├── run.py
│   ├── app/                            # 主应用代码
│   ├── alembic/                        # 数据库迁移
│   ├── tests/                          # 单元测试
│   └── scripts/                        # 工具脚本
├── frontend/
│   ├── README.md
│   ├── src/                            # 源代码
│   └── package.json
├── templates/                          # 导入模板
│   ├── README.md
│   ├── SUPPORTED_FORMATS.md
│   ├── import_template.json
│   ├── import_template.yaml
│   ├── elements_only_template.json
│   └── testcase_recursive_import_template.json
├── executor/                           # 执行器
└── tools/                              # 工具集
```
