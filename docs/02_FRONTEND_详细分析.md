# TestFlow Frontend - 前端管理界面详细分析

## 项目概述

TestFlow Frontend 是基于 React + TypeScript + Ant Design 构建的现代化单页应用(SPA)，为 TestFlow 自动化测试平台提供可视化管理界面。

### 基本信息
- **框架**: React 18
- **语言**: TypeScript
- **UI库**: Ant Design 5.x
- **状态管理**: React Hooks + Context API
- **路由**: React Router v6
- **HTTP客户端**: Axios
- **端口**: 3002

---

## 技术栈详解

### 核心依赖
```json
{
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "antd": "^5.0.0",
  "react-router-dom": "^6.0.0",
  "axios": "^1.0.0",
  "@ant-design/icons": "^5.0.0"
}
```

### 开发工具
- **Vite**: 快速构建工具
- **ESLint**: 代码检查
- **Prettier**: 代码格式化
- **TailwindCSS**: 原子化CSS (可选)

---

## 项目结构

```
frontend/src/
├── pages/              # 页面组件
│   ├── Dashboard/      # 仪表盘
│   ├── Projects/       # 项目管理
│   ├── Screens/        # 界面管理
│   ├── Elements/       # 元素管理
│   ├── Steps/          # 步骤管理
│   ├── Flows/          # 流程管理
│   ├── Testcases/      # 测试用例
│   ├── Suites/         # 测试套件
│   ├── Runs/           # 执行管理
│   ├── History/        # 执行历史
│   ├── Devices/        # 设备管理
│   ├── Scheduler/      # 调度器
│   ├── Users/          # 用户管理
│   └── Login/          # 登录
├── components/         # 公共组件
│   ├── DOMViewer/      # DOM查看器
│   ├── BatchImportWizard/  # 批量导入向导
│   └── ...
├── services/           # API服务
│   ├── api.ts          # 基础API配置
│   ├── element.ts      # 元素API
│   ├── flow.ts         # 流程API
│   ├── testcase.ts     # 用例API
│   ├── ai.ts           # AI API
│   └── device.ts       # 设备API
├── utils/              # 工具函数
├── types/              # TypeScript类型
└── App.tsx             # 应用入口
```

---

## 核心页面功能

### 1. Dashboard (仪表盘)

#### 功能概述
- 测试执行统计概览
- 最近执行记录
- 资源数量统计
- 系统健康状态

#### 核心组件
```tsx
// 统计卡片
<Statistic
  title="总测试用例"
  value={stats.totalTestcases}
  prefix={<FileTextOutlined />}
/>

// 执行趋势图
<Line
  data={executionTrend}
  xField="date"
  yField="count"
/>

// 最近执行列表
<Table
  dataSource={recentRuns}
  columns={runColumns}
/>
```

#### 数据流
```
页面加载 → useEffect
  ↓
并行请求多个API:
  - /api/v1/stats/overview
  - /api/v1/runs/recent
  - /api/v1/health
  ↓
更新状态 → 渲染界面
```

---

### 2. Projects (项目管理)

#### 功能特性
- 项目CRUD操作
- 项目成员管理
- 项目资源统计
- 项目切换

#### 核心表格
```tsx
<Table
  dataSource={projects}
  columns={[
    { title: '名称', dataIndex: 'name' },
    { title: '描述', dataIndex: 'description' },
    { title: '用例数', dataIndex: 'testcaseCount' },
    { title: '创建时间', dataIndex: 'createdAt' },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button onClick={() => handleEdit(record)}>编辑</Button>
          <Button onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      )
    }
  ]}
/>
```

#### 表单验证
```tsx
<Form
  form={form}
  onFinish={handleSubmit}
>
  <Form.Item
    name="name"
    label="项目名称"
    rules={[
      { required: true, message: '请输入项目名称' },
      { min: 2, max: 100 }
    ]}
  >
    <Input placeholder="例如: 移动银行App测试" />
  </Form.Item>

  <Form.Item
    name="description"
    label="项目描述"
  >
    <Input.TextArea rows={4} />
  </Form.Item>
</Form>
```

---

### 3. Elements (元素管理)

#### 功能亮点
- **DOM查看器集成**: 从设备DOM直接创建元素
- **AI智能推荐**: 自动查找相似元素
- **定位符管理**: 支持多种定位符类型
- **元素复用**: 跨流程、跨用例复用

#### DOMViewer组件

**核心功能**:
```tsx
// 1. 获取设备DOM
const fetchDom = async () => {
  const response = await getDeviceDom(deviceSerial);
  const xmlData = response.data.data.dom_xml;

  // 2. 解析XML为树
  const treeData = parseXmlToTree(xmlData);

  // 3. 渲染DOM树
  setTreeData(treeData);
};

// 3. AI推荐相似元素
const fetchAISuggestions = async (selectedElement) => {
  const response = await aiService.suggestElements({
    dom_element: selectedElement,
    threshold: 0.7
  });

  setAiSuggestions(response.matches);

  // 高置信度自动选择
  if (response.best_match?.similarity_score > 0.85) {
    handleSelectMatch(response.best_match);
  }
};
```

**UI布局**:
```
┌─────────────────────────────────────────────┐
│  左侧: DOM树 (14列)    │  右侧: 元素详情 (10列) │
│  ┌──────────────────┐  │  ┌──────────────────┐ │
│  │ 搜索框           │  │  │ 元素属性         │ │
│  ├──────────────────┤  │  │ - 文本           │ │
│  │ 📁 FrameLayout   │  │  │ - Resource ID    │ │
│  │   📁 LinearLayout│  │  │ - Class          │ │
│  │     ✅ 按钮      │  │  │ - Bounds         │ │
│  │     📄 TextView  │  │  │ - Clickable      │ │
│  │                  │  │  │                  │ │
│  │ [刷新DOM]        │  │  │ [添加到元素库]    │ │
│  └──────────────────┘  │  └──────────────────┘ │
└─────────────────────────────────────────────┘
```

**AI增强元素表单**:
```tsx
<Modal title="添加到元素库">
  <Space direction="vertical">
    {/* AI推荐面板 */}
    {aiSuggestions?.matches.length > 0 && (
      <Card title="AI发现相似元素">
        <List
          dataSource={aiSuggestions.matches}
          renderItem={(match) => (
            <List.Item
              actions={[
                <Button onClick={() => handleSelectMatch(match)}>
                  使用
                </Button>
              ]}
            >
              <List.Item.Meta
                title={match.element_name}
                description={
                  <>
                    <Tag color="blue">相似度: {match.similarity_score}</Tag>
                    <div>{match.reason}</div>
                  </>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    )}

    {/* 元素表单 */}
    <Form form={form}>
      <Form.Item name="name" label="元素名称">
        <Input placeholder="AI已自动填充" />
      </Form.Item>
      <Form.Item name="locators" label="定位符">
        <Input.TextArea
          value={JSON.stringify(locators, null, 2)}
          disabled
        />
      </Form.Item>
    </Form>
  </Space>
</Modal>
```

---

### 4. Flows (流程管理)

#### 功能特性
- **流程设计器**: 可视化流程编辑
- **步骤编排**: 拖拽排序步骤
- **流程复制**: 快速创建相似流程
- **流程预览**: 实时预览执行效果

#### 流程编辑器
```tsx
<FlowDesigner>
  {/* 步骤列表 */}
  <StepsList
    steps={flowSteps}
    onReorder={handleReorder}
    renderStep={(step) => (
      <StepCard
        step={step}
        actions={[
          <Button onClick={() => editStep(step)}>编辑</Button>,
          <Button onClick={() => deleteStep(step.id)}>删除</Button>
        ]}
      >
        <StepDetail step={step} />
      </StepCard>
    )}
  />

  {/* 添加步骤 */}
  <Button
    type="dashed"
    onClick={() => setAddStepVisible(true)}
  >
    + 添加步骤
  </Button>
</FlowDesigner>
```

#### 步骤类型支持
```tsx
enum StepType {
  // 设备操作
  CLICK = 'click',
  LONG_PRESS = 'long_press',
  INPUT = 'input',
  SWIPE = 'swipe',

  // 等待操作
  WAIT_ELEMENT = 'wait_element',
  WAIT_TIME = 'wait_time',

  // 断言操作
  ASSERT_TEXT = 'assert_text',
  ASSERT_EXISTS = 'assert_exists',
  ASSERT_NOT_EXISTS = 'assert_not_exists',

  // 系统操作
  START_ACTIVITY = 'start_activity',
  SCREENSHOT = 'screenshot',
  HARDWARE_BACK = 'hardware_back'
}
```

---

### 5. Testcases (测试用例管理)

#### 功能亮点
- **AI智能生成**: 从描述生成完整用例
- **批量导入**: JSON/YAML文件导入
- **用例复用**: Setup/Main/Teardown流程组合
- **标签管理**: 多维度标签分类

#### AI生成向导
```tsx
<AIImportWizard>
  {/* Step 1: 上传JSON */}
  <UploadStep>
    <Dragger
      accept=".json,.yaml"
      beforeUpload={handleFileUpload}
    >
      <p>点击或拖拽JSON文件到此区域</p>
    </Dragger>

    <TextArea
      rows={12}
      placeholder="粘贴JSON描述..."
      onChange={(e) => setJsonInput(e.target.value)}
    />

    <Space>
      <Button onClick={() => handleAnalyze(true)}>
        跳过AI修正
      </Button>
      <Button
        type="primary"
        icon={<ThunderboltOutlined />}
        onClick={() => handleAnalyze(false)}
      >
        AI修正格式
      </Button>
    </Space>
  </UploadStep>

  {/* Step 2: AI分析结果 */}
  <AnalysisResult>
    <Row gutter={16}>
      <Col span={8}>
        <Statistic
          title="测试用例数量"
          value={correctedData.testcases?.length}
        />
      </Col>
      <Col span={8}>
        <Statistic
          title="修正的字段"
          value={correctedData.corrections?.length}
        />
      </Col>
      <Col span={8}>
        <Statistic
          title="需要人工确认"
          value={correctedData.needs_review}
        />
      </Col>
    </Row>

    {/* AI修正说明 */}
    <List
      dataSource={correctedData.corrections}
      renderItem={(correction) => (
        <List.Item>
          <List.Item.Meta
            title={<Tag color="blue">{correction.field}</Tag>}
            description={
              <>
                <Text type="danger">原值: {correction.old_value}</Text>
                <Text type="success">新值: {correction.new_value}</Text>
              </>
            }
          />
        </List.Item>
      )}
    />
  </AnalysisResult>

  {/* Step 3: 确认导入 */}
  <ConfirmStep>
    <Button
      type="primary"
      onClick={handleImport}
      loading={importing}
    >
      确认导入
    </Button>
  </ConfirmStep>
</AIImportWizard>
```

#### 用例详情页
```tsx
<TestcaseDetail testcase={testcase}>
  <Tabs>
    <TabPane tab="基本信息" key="info">
      <Descriptions>
        <Descriptions.Item label="名称">
          {testcase.name}
        </Descriptions.Item>
        <Descriptions.Item label="优先级">
          <Tag color={priorityColor[testcase.priority]}>
            {testcase.priority}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="超时时间">
          {testcase.timeout}秒
        </Descriptions.Item>
      </Descriptions>
    </TabPane>

    <TabPane tab="前置流程" key="setup">
      <FlowList flows={testcase.setup_flows} />
    </TabPane>

    <TabPane tab="主流程" key="main">
      <FlowList flows={testcase.main_flows} />
    </TabPane>

    <TabPane tab="清理流程" key="teardown">
      <FlowList flows={testcase.teardown_flows} />
    </TabPane>

    <TabPane tab="执行历史" key="history">
      <RunHistory testcaseId={testcase.id} />
    </TabPane>
  </Tabs>
</TestcaseDetail>
```

---

### 6. Runs (执行管理)

#### 实时执行监控
```tsx
// WebSocket连接
useEffect(() => {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/runs/${runId}`);

  ws.onmessage = (event) => {
    const log = JSON.parse(event.data);
    setLogs((prev) => [...prev, log]);

    // 自动滚动到底部
    logContainerRef.current?.scrollTo({
      top: logContainerRef.current.scrollHeight,
      behavior: 'smooth'
    });
  };

  return () => ws.close();
}, [runId]);

// 日志渲染
<LogViewer>
  {logs.map((log, index) => (
    <LogEntry
      key={index}
      level={log.level}
      timestamp={log.timestamp}
    >
      <LogMessage>{log.message}</LogMessage>
      {log.screenshot && (
        <Screenshot src={log.screenshot} />
      )}
    </LogEntry>
  ))}
</LogViewer>
```

#### 执行控制
```tsx
<Space>
  <Button
    icon={<PlayCircleOutlined />}
    onClick={handleStart}
    disabled={status !== 'pending'}
  >
    开始执行
  </Button>

  <Button
    icon={<PauseCircleOutlined />}
    onClick={handlePause}
    disabled={status !== 'running'}
  >
    暂停
  </Button>

  <Button
    icon={<StopOutlined />}
    onClick={handleCancel}
    disabled={status === 'completed'}
  >
    取消
  </Button>

  <Button
    icon={<DownloadOutlined />}
    onClick={handleDownloadReport}
  >
    下载报告
  </Button>
</Space>

{/* 进度条 */}
<Progress
  percent={progress}
  status={status}
  strokeColor={{
    '0%': '#108ee9',
    '100%': '#87d068'
  }}
/>
```

---

### 7. Devices (设备管理)

#### 设备列表
```tsx
<Table
  dataSource={devices}
  columns={[
    {
      title: '序列号',
      dataIndex: 'serial'
    },
    {
      title: '状态',
      render: (_, record) => (
        <Tag color={record.status === 'online' ? 'success' : 'default'}>
          {record.status}
        </Tag>
      )
    },
    {
      title: '品牌/型号',
      render: (_, record) => `${record.brand} ${record.model}`
    },
    {
      title: 'Android版本',
      dataIndex: 'android_version'
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            onClick={() => openDOMViewer(record)}
          >
            DOM查看
          </Button>
          <Button
            size="small"
            onClick={() => captureScreenshot(record)}
          >
            截图
          </Button>
        </Space>
      )
    }
  ]}
/>
```

#### 实时设备状态
```tsx
// WebSocket设备状态
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/api/v1/ws/devices');

  ws.onmessage = (event) => {
    const deviceStatus = JSON.parse(event.data);
    setDevices((prev) =>
      prev.map((d) =>
        d.serial === deviceStatus.serial
          ? { ...d, ...deviceStatus }
          : d
      )
    );
  };

  return () => ws.close();
}, []);
```

---

### 8. Scheduler (调度器)

#### 定时任务配置
```tsx
<Form form={form}>
  <Form.Item
    name="name"
    label="任务名称"
    rules={[{ required: true }]}
  >
    <Input placeholder="例如: 每日回归测试" />
  </Form.Item>

  <Form.Item
    name="cron"
    label="Cron表达式"
    rules={[{ required: true }]}
  >
    <CronPicker
      placeholder="0 2 * * *"
      onChange={setCronValue}
    />
  </Form.Item>

  <CronPreview value={cronValue}>
    下次执行: {nextRunTime}
  </CronPreview>

  <Form.Item
    name="suite_id"
    label="测试套件"
    rules={[{ required: true }]}
  >
    <Select
      showSearch
      options={suites}
    />
  </Form.Item>

  <Form.Item
    name="device_serial"
    label="执行设备"
  >
    <DeviceSelector />
  </Form.Item>
</Form>
```

#### 调度历史
```tsx
<Timeline>
  {jobHistory.map((job) => (
    <Timeline.Item
      key={job.id}
      color={job.status === 'success' ? 'green' : 'red'}
    >
      <p>
        <strong>{job.triggered_at}</strong>
      </p>
      <p>状态: {job.status}</p>
      <p>执行时长: {job.duration}</p>
      <p>
        <Button size="small" onClick={() => viewJobLogs(job)}>
          查看日志
        </Button>
      </p>
    </Timeline.Item>
  ))}
</Timeline>
```

---

## 核心组件详解

### 1. DOMViewer (DOM查看器)

**功能**:
- 解析设备DOM XML为可视化树
- 支持元素搜索和过滤
- 集成AI元素推荐
- 一键添加到元素库

**核心技术**:
```tsx
// XML解析
const parseXmlToTree = (xmlString: string): TreeNode[] => {
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(xmlString, "text/xml");

  const traverse = (node: Element): TreeNode => {
    const attributes: Record<string, string> = {};
    for (let i = 0; i < node.attributes.length; i++) {
      const attr = node.attributes[i];
      attributes[attr.name] = attr.value;
    }

    return {
      key: generateKey(),
      title: buildNodeTitle(attributes),
      element: attributes,
      children: Array.from(node.children).map(traverse)
    };
  };

  return Array.from(xmlDoc.children).map(traverse);
};

// 树节点标题渲染
const buildNodeTitle = (element: DomElement): ReactNode => {
  const tags = [];
  if (element.clickable === 'true') {
    tags.push(<Tag color="blue">可点击</Tag>);
  }
  if (element.text) {
    tags.push(<Tag color="green">文本</Tag>);
  }

  return (
    <Space size={4}>
      {...tags}
      <Text ellipsis>{element.text || element['resource-id']}</Text>
    </Space>
  );
};
```

**状态管理**:
```tsx
const [domXml, setDomXml] = useState('');
const [treeData, setTreeData] = useState<TreeNode[]>([]);
const [selectedElement, setSelectedElement] = useState<DomElement | null>(null);
const [searchText, setSearchText] = useState('');
const [aiSuggestions, setAiSuggestions] = useState(null);
const [aiAnalyzing, setAiAnalyzing] = useState(false);
```

---

### 2. BatchImportWizard (批量导入向导)

**多步骤流程**:
```tsx
const [currentStep, setCurrentStep] = useState(0);

const steps = [
  { title: '上传JSON', description: '导入测试用例' },
  { title: 'AI修正', description: '优化格式' },
  { title: '确认导入', description: '批量创建' }
];

<Steps current={currentStep}>
  {steps.map(step => (
    <Step key={step.title} {...step} />
  ))}
</Steps>
```

**AI修正逻辑**:
```tsx
const handleAnalyze = async (skipAI = false) => {
  if (skipAI) {
    // 跳过AI，直接使用原始数据
    setCorrectedData({
      testcases: Array.isArray(jsonData) ? jsonData : [jsonData],
      corrections: [],
      warnings: [],
      needs_review: 0
    });
  } else {
    // 调用AI修正
    const response = await aiService.correctJSON(jsonData);
    setCorrectedData(response.data);

    // 显示修正统计
    message.success(`AI修正完成！修正了 ${response.data.corrections.length} 个字段`);
  }

  setCurrentStep(1);
};
```

**批量导入**:
```tsx
const handleImport = async () => {
  const response = await testcaseService.batchCreate({
    testcases: correctedData.testcases,
    project_id: projectId
  });

  message.success(`成功导入 ${response.data.count} 个测试用例`);

  setCurrentStep(2);
  setTimeout(() => {
    onSuccess(response.data.count);
  }, 1500);
};
```

---

### 3. LogViewer (日志查看器)

**实时日志流**:
```tsx
const LogViewer: React.FC<LogViewerProps> = ({ runId }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<LogFilter>({
    level: 'ALL',
    search: ''
  });

  // WebSocket连接
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/runs/${runId}`);

    ws.onmessage = (event) => {
      const log = JSON.parse(event.data);

      // 过滤
      if (filter.level !== 'ALL' && log.level !== filter.level) {
        return;
      }

      setLogs((prev) => [...prev, log]);
    };

    return () => ws.close();
  }, [runId, filter]);

  return (
    <div className="log-viewer">
      <LogFilter onChange={setFilter} />
      <LogContainer ref={logContainerRef}>
        {logs.map((log, index) => (
          <LogRow key={index} level={log.level}>
            <LogTimestamp>{log.timestamp}</LogTimestamp>
            <LogLevel level={log.level}>{log.level}</LogLevel>
            <LogMessage>{log.message}</LogMessage>
            {log.screenshot && (
              <LogScreenshot src={log.screenshot} />
            )}
          </LogRow>
        ))}
      </LogContainer>
    </div>
  );
};
```

---

## 服务层架构

### API服务封装

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data;
    if (code === 0) {
      return { data, message };
    }
    message.error(message);
    return Promise.reject(new Error(message));
  },
  (error) => {
    if (error.response?.status === 401) {
      // 跳转登录
      window.location.href = '/login';
    }
    message.error(error.message);
    return Promise.reject(error);
  }
);

export default api;
```

### 业务API模块

```typescript
// services/element.ts
import api from './api';

export const elementService = {
  // 获取元素列表
  list: (params: ElementQueryParams) => {
    return api.get('/elements', { params });
  },

  // 创建元素
  create: (data: ElementCreate) => {
    return api.post('/elements', data);
  },

  // 更新元素
  update: (id: number, data: ElementUpdate) => {
    return api.put(`/elements/${id}`, data);
  },

  // 删除元素
  delete: (id: number) => {
    return api.delete(`/elements/${id}`);
  },

  // 批量导入
  batchImport: (elements: ElementCreate[]) => {
    return api.post('/elements/batch', { elements });
  }
};

// services/ai.ts
export const aiService = {
  // AI元素推荐
  suggestElements: (data: ElementSuggestRequest) => {
    return api.post('/ai/elements/suggest', data);
  },

  // AI用例生成
  generateTestcase: (data: TestcaseGenerateRequest) => {
    return api.post('/ai/testcases/generate', data);
  },

  // AI配置
  getConfig: () => {
    return api.get('/ai/config/active');
  },

  // 测试AI连接
  testConfig: (config: AIConfig) => {
    return api.post('/ai/config/test', config);
  }
};
```

---

## 状态管理

### Context API + Hooks

```typescript
// contexts/AppContext.tsx
interface AppContextType {
  currentUser: User | null;
  currentProject: Project | null;
  devices: Device[];
  updateCurrentUser: (user: User) => void;
  updateCurrentProject: (project: Project) => void;
}

export const AppContext = createContext<AppContextType>({
  currentUser: null,
  currentProject: null,
  devices: [],
  updateCurrentUser: () => {},
  updateCurrentProject: () => {}
});

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);

  // 加载当前用户
  useEffect(() => {
    loadCurrentUser();
  }, []);

  // 轮询设备状态
  useEffect(() => {
    const interval = setInterval(() => {
      loadDevices();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider
      value={{
        currentUser,
        currentProject,
        devices,
        updateCurrentUser: setCurrentUser,
        updateCurrentProject: setCurrentProject
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

// 使用Context
const { currentProject } = useAppContext();
```

---

## 路由配置

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 公共路由 */}
        <Route path="/login" element={<Login />} />

        {/* 受保护路由 */}
        <Route path="/" element={<ProtectedLayout><Dashboard /></ProtectedLayout>} />
        <Route path="/projects" element={<ProtectedLayout><Projects /></ProtectedLayout>} />
        <Route path="/elements" element={<ProtectedLayout><Elements /></ProtectedLayout>} />
        <Route path="/flows" element={<ProtectedLayout><Flows /></ProtectedLayout>} />
        <Route path="/testcases" element={<ProtectedLayout><Testcases /></ProtectedLayout>} />
        <Route path="/runs" element={<ProtectedLayout><Runs /></ProtectedLayout>} />
        <Route path="/devices" element={<ProtectedLayout><Devices /></ProtectedLayout>} />
        <Route path="/scheduler" element={<ProtectedLayout><Scheduler /></ProtectedLayout>} />

        {/* 默认重定向 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

// 受保护布局
const ProtectedLayout: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { currentUser } = useAppContext();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Layout>
      <AppSidebar />
      <Layout>
        <AppHeader />
        <Content>{children}</Content>
      </Layout>
    </Layout>
  );
};
```

---

## UI/UX特色

### 1. 响应式布局
```tsx
<Row gutter={[16, 16]}>
  <Col xs={24} sm={12} md={8} lg={6}>
    {/* 移动端占满，平板12列，桌面8列，大屏6列 */}
  </Col>
</Row>
```

### 2. 加载状态
```tsx
<Spin spinning={loading} tip="加载中...">
  <Card>内容</Card>
</Spin>
```

### 3. 错误处理
```tsx
try {
  await apiCall();
} catch (error: any) {
  notification.error({
    message: '操作失败',
    description: error.response?.data?.message || error.message
  });
}
```

### 4. 确认对话框
```tsx
Modal.confirm({
  title: '确认删除',
  content: '删除后无法恢复，确定要删除吗？',
  okText: '确定',
  cancelText: '取消',
  onOk: async () => {
    await deleteTestcase(id);
    message.success('删除成功');
  }
});
```

### 5. 表格编辑
```tsx
const [editingKey, setEditingKey] = useState('');

const isEditing = (record: Testcase) => record.id === editingKey;

const columns = [
  {
    title: '名称',
    dataIndex: 'name',
    editable: true,
    render: (text: string, record: Testcase) => {
      if (isEditing(record)) {
        return (
          <Input
            defaultValue={text}
            onPressEnter={(e) => save(record.id, e.currentTarget.value)}
          />
        );
      }
      return text;
    }
  },
  {
    title: '操作',
    render: (_: any, record: Testcase) => {
      if (isEditing(record)) {
        return (
          <Space>
            <Button onClick={() => save()}>保存</Button>
            <Button onClick={() => cancel()}>取消</Button>
          </Space>
        );
      }
      return (
        <Button onClick={() => edit(record)}>编辑</Button>
      );
    }
  }
];
```

---

## 性能优化

### 1. 代码分割
```typescript
// 路由懒加载
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Testcases = lazy(() => import('./pages/Testcases'));

<Suspense fallback={<Spin />}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/testcases" element={<Testcases />} />
  </Routes>
</Suspense>
```

### 2. 虚拟滚动
```tsx
import { List } from 'react-virtualized';

<List
  width={800}
  height={600}
  rowCount={data.length}
  rowHeight={50}
  rowRenderer={({ index, key, style }) => (
    <div key={key} style={style}>
      {data[index]}
    </div>
  )}
/>
```

### 3. 防抖与节流
```typescript
import { debounce } from 'lodash';

const handleSearch = debounce((value: string) => {
  fetchData(value);
}, 300);

<Input onChange={(e) => handleSearch(e.target.value)} />
```

### 4. 记忆化
```typescript
const memoizedValue = useMemo(() => {
  return expensiveComputation(props.data);
}, [props.data]);

const memoizedCallback = useCallback(() => {
  doSomething(dependency);
}, [dependency]);
```

---

## 总结

TestFlow Frontend 是一个功能完善、用户体验优秀的现代化管理界面，具有以下核心优势：

1. **完整的测试管理界面**: 从元素到套件的全套CRUD操作
2. **AI智能增强**: DOM查看器AI推荐、批量导入AI修正
3. **实时执行监控**: WebSocket日志流、进度可视化
4. **优秀的交互体验**: 响应式布局、加载状态、错误处理
5. **可扩展性**: 组件化设计，易于添加新功能
6. **类型安全**: TypeScript全覆盖，减少运行时错误

适用于中小型团队的Android自动化测试管理需求，特别适合需要快速创建和管理大量测试用例的场景。
