# TestFlow Backend - 单元测试

## 测试覆盖

本测试套件覆盖了 TestFlow 后端的所有核心 API 接口：

### 测试文件

| 文件 | 描述 | 测试用例数 |
|------|------|-----------|
| `test_elements.py` | 元素接口测试 | 18 |
| `test_steps.py` | 步骤接口测试 | 11 |
| `test_flows.py` | 流程接口测试 | 23 |
| `test_testcases.py` | 用例接口测试 | 18 |
| `test_runs.py` | 执行接口测试 | 24 |

**总计**: 94+ 个测试用例

### 测试覆盖范围

#### 元素接口 (test_elements.py)
- ✅ 列表查询（分页、筛选、搜索）
- ✅ CRUD 操作
- ✅ 定位符测试
- ✅ 边界条件和错误处理

#### 步骤接口 (test_steps.py)
- ✅ 创建不同类型的步骤 (click, input, assert_text)
- ✅ 元素和界面关联验证
- ✅ 断言配置验证
- ✅ 删除依赖检查

#### 流程接口 (test_flows.py)
- ✅ 三种流程类型 (standard/dsl/python)
- ✅ DSL 验证和解析
- ✅ 流程复制
- ✅ 依赖检查

#### 用例接口 (test_testcases.py)
- ✅ 用例 CRUD
- ✅ 三种流程角色 (setup/main/teardown)
- ✅ 标签关联
- ✅ 参数传递
- ✅ 依赖链查询

#### 执行接口 (test_runs.py)
- ✅ 启动测试执行
- ✅ 执行控制（停止、暂停、恢复）
- ✅ 状态查询
- ✅ SSE 日志流
- ✅ 批量执行

## 环境要求

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-asyncio
```

## 运行测试

### 运行所有测试
```bash
cd testflow/backend
pytest tests/
```

### 运行特定测试文件
```bash
pytest tests/test_elements.py
```

### 运行特定测试类
```bash
pytest tests/test_elements.py::TestElementsCreate
```

### 运行特定测试方法
```bash
pytest tests/test_elements.py::TestElementsCreate::test_create_element_success
```

### 查看详细输出
```bash
pytest tests/ -v
```

### 显示打印输出
```bash
pytest tests/ -v -s
```

### 生成覆盖率报告
```bash
pytest tests/ --cov=app --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

### 并行运行测试（需要安装 pytest-xdist）
```bash
pytest tests/ -n auto
```

## 测试数据

### Fixtures

测试使用 pytest fixtures 来创建测试数据：

```python
@pytest.fixture
def screen(db: Session):
    """预建界面记录"""
    # 自动创建一个测试界面

@pytest.fixture
def element(db: Session, screen):
    """预建元素记录"""
    # 自动创建一个测试元素（关联到 screen）

@pytest.fixture
def step(db: Session, screen, element):
    """预建步骤记录"""
    # 自动创建一个测试步骤

@pytest.fixture
def flow(db: Session, step):
    """预建流程记录"""
    # 自动创建一个测试流程

@pytest.fixture
def testcase(db: Session, flow):
    """预建用例记录"""
    # 自动创建一个测试用例

@pytest.fixture
def profile(db: Session):
    """预建 Profile 记录"""
    # 自动创建一个测试配置

@pytest.fixture
def device(db: Session):
    """预建设备记录"""
    # 自动创建一个测试设备

@pytest.fixture
def tag(db: Session):
    """预建标签记录"""
    # 自动创建一个测试标签

@pytest.fixture
def suite(db: Session):
    """预建套件记录"""
    # 自动创建一个测试套件
```

### Mock Fixtures

```python
@pytest.fixture
def mock_adb_devices(monkeypatch):
    """Mock ADB 设备列表"""

@pytest.fixture
def mock_adb_check_online(monkeypatch):
    """Mock ADB 设备在线检查"""

@pytest.fixture
def mock_adb_find_element(monkeypatch):
    """Mock ADB 元素查找"""
```

### Factory 模式

使用 `TestDataFactory` 快速创建测试数据：

```python
from tests.factories import TestDataFactory

# 创建界面
screen = TestDataFactory.create_screen(db, name="MyScreen")

# 创建元素（含定位符）
element = TestDataFactory.create_element(
    db,
    screen_id=screen.id,
    name="myElement",
    locators=[
        {"type": "resource-id", "value": "com.app:id/btn", "priority": 1}
    ]
)

# 创建流程（含步骤）
flow = TestDataFactory.create_flow(
    db,
    name="MyFlow",
    steps=[
        {"step_id": step1.id, "order": 1},
        {"step_id": step2.id, "order": 2}
    ]
)
```

## 测试数据库

测试使用 SQLite 内存数据库，每个测试函数：

1. 创建所有表
2. 提供独立的数据库会话
3. 测试结束后自动清理（回滚事务并删除表）

这确保测试之间完全隔离，不会相互影响。

## 命名规范

测试用例按照文档中的测试用例 ID 命名：

- `TC-EL-001` → `test_create_element_success`
- `TC-ST-001` → `test_create_click_step_success`
- `TC-FL-001` → `test_create_standard_flow_success`
- `TC-TC-001` → `test_create_testcase_success`
- `TC-RN-001` → `test_start_testcase_run_success`

## 添加新测试

1. 在相应的测试文件中添加测试方法
2. 使用 fixtures 获取测试数据
3. 使用 `client` 发送请求
4. 断言响应状态码和数据

```python
def test_my_new_feature(
    self,
    client: TestClient,
    db: Session,
    screen  # 使用 fixture
):
    """TC-XX-001: 测试描述"""
    response = client.post(
        "/api/v1/endpoint",
        json={"key": "value"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 0
    assert "expected_field" in data["data"]
```

## 常见问题

### 导入错误

确保在 `testflow/backend` 目录下运行测试，或使用 `PYTHONPATH`：

```bash
cd testflow/backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/
```

### 数据库错误

测试使用内存数据库，不需要 MySQL。如果遇到数据库错误，检查 `conftest.py` 中的 `db` fixture。

### Mock 不生效

确保在测试参数中包含 `monkeypatch` fixture：

```python
def test_with_mock(self, client, db, monkeypatch):
    # 使用 monkeypatch 修改
    pass
```

## 持续集成

测试可以在 CI/CD 流水线中运行：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    cd testflow/backend
    pytest tests/ --cov=app --cov-report=xml
```

## 下一步

- [ ] 添加集成测试（使用真实数据库）
- [ ] 添加性能测试
- [ ] 添加端到端测试
- [ ] 提高测试覆盖率到 90%+
