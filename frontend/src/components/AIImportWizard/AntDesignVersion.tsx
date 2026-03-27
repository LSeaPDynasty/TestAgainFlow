/**
 * AI Import Wizard - Ant Design Version
 * JSON-based test case generation using Ant Design components
 */

import React, { useState } from 'react';
import {
  Modal,
  Steps,
  Input,
  Button,
  Space,
  Alert,
  Card,
  Tag,
  List,
  message,
  Spin,
  Divider,
  Typography,
  Switch,
  Empty,
} from 'antd';
import {
  ThunderboltOutlined,
  CheckOutlined,
  CloseOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { aiService, type TestcaseGenerateResponse } from '../../services/ai';

const { TextArea } = Input;
const { Text, Paragraph, Title } = Typography;

interface AIImportWizardProps {
  projectId?: number;
  onSuccess: (testcase: any) => void;
  onCancel: () => void;
}

export const AIImportWizard: React.FC<AIImportWizardProps> = ({
  projectId,
  onSuccess,
  onCancel,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [jsonInput, setJsonInput] = useState('');
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<TestcaseGenerateResponse | null>(null);
  const [creating, setCreating] = useState(false);
  const [autoCreate, setAutoCreate] = useState(false);

  const steps = [
    {
      title: '上传JSON',
      description: '描述测试用例',
    },
    {
      title: 'AI分析',
      description: '智能匹配资源',
    },
    {
      title: '查看方案',
      description: '确认测试结构',
    },
    {
      title: '完成',
      description: '创建测试用例',
    },
  ];

  const validateJson = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      setJsonError(null);
      return parsed;
    } catch (err: any) {
      setJsonError(err.message);
      return null;
    }
  };

  const handleAnalyze = async () => {
    const jsonData = validateJson();
    if (!jsonData) {
      message.error('JSON格式错误，请检查输入');
      return;
    }

    setAnalyzing(true);
    setJsonError(null);

    try {
      const response = await aiService.generateTestcase({
        json_data: jsonData,
        project_id: projectId,
      });

      setResult(response);
      setCurrentStep(1);
      message.success('AI分析完成！');
    } catch (err: any) {
      console.error('AI分析失败:', err);
      message.error(err.response?.data?.message || 'AI分析失败，请重试');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCreate = async () => {
    if (!result?.plan) return;

    setCreating(true);

    try {
      // 这里需要调用创建测试用例的API
      // 暂时传递plan数据，实际需要根据API结构调整
      await onSuccess(result.plan);

      setCurrentStep(3);
      message.success('测试用例创建成功！');
    } catch (err: any) {
      console.error('创建测试用例失败:', err);
      message.error(err.response?.data?.message || '创建测试用例失败');
    } finally {
      setCreating(false);
    }
  };

  const loadSampleJson = () => {
    const sample = {
      testcase_name: '用户登录流程',
      description: '验证用户可以使用有效凭据成功登录',
      steps_description: [
        '打开登录界面',
        '在用户名字段输入用户名',
        '在密码字段输入密码',
        '点击登录按钮',
        '验证主界面已显示',
      ],
    };
    setJsonInput(JSON.stringify(sample, null, 2));
    setJsonError(null);
  };

  const resetWizard = () => {
    setCurrentStep(0);
    setJsonInput('');
    setJsonError(null);
    setResult(null);
    setAutoCreate(false);
  };

  const handleClose = () => {
    resetWizard();
    onCancel();
  };

  const renderUploadStep = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Paragraph type="secondary">
        上传JSON格式的测试用例描述，AI将自动分析并生成最优的测试用例结构。
      </Paragraph>

      <TextArea
        rows={15}
        placeholder={`{
  "testcase_name": "我的测试用例",
  "description": "测试用例描述",
  "steps_description": [
    "步骤1描述",
    "步骤2描述"
  ]
}`}
        value={jsonInput}
        onChange={(e) => setJsonInput(e.target.value)}
        status={jsonError ? 'error' : undefined}
        style={{ fontFamily: 'monospace' }}
      />

      {jsonError && (
        <Alert
          message="JSON格式错误"
          description={jsonError}
          type="error"
          showIcon
          closable
        />
      )}

      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Button onClick={loadSampleJson}>加载示例</Button>
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          onClick={handleAnalyze}
          disabled={!jsonInput.trim() || analyzing}
          loading={analyzing}
        >
          {analyzing ? '分析中...' : 'AI分析'}
        </Button>
      </Space>
    </Space>
  );

  const renderAnalysisStep = () => {
    if (!result) return null;

    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Alert
          message="分析完成"
          description={
            result.ai_stats ? (
              <Space>
                <Text>耗时: {result.ai_stats.latency_ms}ms</Text>
                <Text>成本: ${result.ai_stats.cost_usd?.toFixed(4)}</Text>
              </Space>
            ) : null
          }
          type="success"
          showIcon
        />

        {/* 分析摘要 */}
        {result.analysis && (
          <Card title="分析摘要" size="small">
            {result.analysis.goal && (
              <Paragraph>
                <Text strong>目标：</Text>
                {result.analysis.goal}
              </Paragraph>
            )}
            {result.analysis.key_actions && result.analysis.key_actions.length > 0 && (
              <div>
                <Text strong>关键操作：</Text>
                <List
                  size="small"
                  dataSource={result.analysis.key_actions}
                  renderItem={(action) => <List.Item>• {action}</List.Item>}
                />
              </div>
            )}
          </Card>
        )}

        {/* 找到的资源 */}
        <Card title="找到的资源" size="small">
          <Space>
            <Tag color="blue">{result.resources_found.elements} 个元素</Tag>
            <Tag color="green">{result.resources_found.steps} 个步骤</Tag>
            <Tag color="orange">{result.resources_found.flows} 个流程</Tag>
          </Space>
        </Card>

        {/* AI推荐 */}
        {result.recommendations.length > 0 && (
          <Card title="AI推荐" size="small">
            <List
              dataSource={result.recommendations}
              renderItem={(rec, index) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Tag color={rec.type.startsWith('reuse') ? 'success' : 'processing'}>
                          {rec.type.replace(/_/g, ' ')}
                        </Tag>
                        <Text strong>{rec.name || `ID: ${rec.flow_id || rec.step_id || rec.element_id}`}</Text>
                        <Tag>{Math.round(rec.confidence * 100)}% 置信度</Tag>
                      </Space>
                    }
                    description={rec.reason}
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* 缺失资源 */}
        {(result.missing_resources.elements.length > 0 || result.missing_resources.steps.length > 0) && (
          <Alert
            message="需要创建的资源"
            description={
              <Space direction="vertical">
                {result.missing_resources.elements.length > 0 && (
                  <Text>• 元素: {result.missing_resources.elements.join(', ')}</Text>
                )}
                {result.missing_resources.steps.length > 0 && (
                  <Text>• 步骤: {result.missing_resources.steps.join(', ')}</Text>
                )}
              </Space>
            }
            type="warning"
            showIcon
          />
        )}
      </Space>
    );
  };

  const renderReviewStep = () => {
    if (!result?.plan) return null;

    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Card title="测试用例计划">
          <Title level={4}>{result.plan.name}</Title>
          <Paragraph type="secondary">{result.plan.description}</Paragraph>
        </Card>

        <Card title="测试用例结构" size="small">
          <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
            {JSON.stringify(result.plan.structure, null, 2)}
          </pre>
        </Card>

        <Card size="small">
          <Space direction="vertical">
            <Text strong>自动创建缺失资源</Text>
            <Switch checked={autoCreate} onChange={setAutoCreate} />
            <Text type="secondary">启用后，系统将自动创建任何缺失的元素或步骤</Text>
          </Space>
        </Card>
      </Space>
    );
  };

  const renderCompleteStep = () => (
    <div style={{ textAlign: 'center', padding: '40px 0' }}>
      <CheckOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 16 }} />
      <Title level={3}>测试用例创建成功！</Title>
      <Paragraph type="secondary">您的测试用例已创建并可以使用。</Paragraph>
    </div>
  );

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderUploadStep();
      case 1:
        return renderAnalysisStep();
      case 2:
        return renderReviewStep();
      case 3:
        return renderCompleteStep();
      default:
        return null;
    }
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 0:
        return !jsonError && jsonInput.trim().length > 0;
      case 1:
        return result?.success === true;
      case 2:
        return result?.plan !== undefined;
      case 3:
        return true;
      default:
        return false;
    }
  };

  return (
    <Modal
      title={
        <Space>
          <ThunderboltOutlined />
          AI智能生成测试用例
        </Space>
      }
      open={true}
      onCancel={handleClose}
      footer={null}
      width={900}
      destroyOnClose
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Steps
          current={currentStep}
          items={steps.map((step) => ({
            title: step.title,
            description: step.description,
          }))}
        />

        <Spin spinning={analyzing || creating} tip={analyzing ? 'AI分析中...' : '创建中...'}>
          {renderStepContent()}
        </Spin>

        <Divider />

        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
          {currentStep === 0 && (
            <>
              <Button onClick={handleClose}>取消</Button>
            </>
          )}
          {currentStep === 1 && isStepValid() && (
            <>
              <Button icon={<ArrowLeftOutlined />} onClick={() => setCurrentStep(0)}>
                上一步
              </Button>
              <Button
                type="primary"
                icon={<ArrowRightOutlined />}
                onClick={() => setCurrentStep(2)}
              >
                查看方案
              </Button>
            </>
          )}
          {currentStep === 2 && isStepValid() && (
            <>
              <Button icon={<ArrowLeftOutlined />} onClick={() => setCurrentStep(1)}>
                上一步
              </Button>
              <Button
                type="primary"
                icon={<CheckOutlined />}
                onClick={handleCreate}
                loading={creating}
              >
                创建测试用例
              </Button>
            </>
          )}
          {currentStep === 3 && (
            <Button type="primary" onClick={handleClose}>
              关闭
            </Button>
          )}
        </Space>
      </Space>
    </Modal>
  );
};

export default AIImportWizard;
