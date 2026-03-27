/**
 * Batch Import Wizard - AI-powered JSON correction and batch import
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
  Upload,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  ThunderboltOutlined,
  CheckOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  UploadOutlined,
  FileTextOutlined,
  DiffOutlined,
} from '@ant-design/icons';
import { aiService } from '../../services/ai';

const { TextArea } = Input;
const { Text, Paragraph, Title } = Typography;
const { Dragger } = Upload;

interface BatchImportWizardProps {
  projectId?: number;
  onSuccess: (count: number) => void;
  onCancel: () => void;
}

export const BatchImportWizard: React.FC<BatchImportWizardProps> = ({
  projectId,
  onSuccess,
  onCancel,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [jsonInput, setJsonInput] = useState('');
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [correctedData, setCorrectedData] = useState<any>(null);
  const [importing, setImporting] = useState(false);

  const steps = [
    {
      title: '上传JSON',
      description: '导入测试用例',
    },
    {
      title: 'AI修正',
      description: '优化格式',
    },
    {
      title: '确认导入',
      description: '批量创建',
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

  const handleAnalyze = async (skipAI = false) => {
    const jsonData = validateJson();
    if (!jsonData) {
      message.error('JSON格式错误，请检查输入');
      return;
    }

    setAnalyzing(true);
    setJsonError(null);

    try {
      if (skipAI) {
        // 跳过AI修正，直接使用原始数据
        setCorrectedData({
          testcases: Array.isArray(jsonData) ? jsonData : [jsonData],
          corrections: [],
          warnings: [],
          needs_review: 0
        });
        setCurrentStep(1);
        message.success('数据验证通过！');
      } else {
        // 调用AI修正JSON
        const response = await fetch('/api/v1/ai/batch-import/correct', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            json_data: jsonData,
            project_id: projectId,
          }),
        });

        const result = await response.json();

        if (result.code === 0) {
          setCorrectedData(result.data);
          setCurrentStep(1);
          message.success('AI修正完成！');
        } else {
          throw new Error(result.message || 'AI修正失败');
        }
      }
    } catch (err: any) {
      console.error('处理失败:', err);
      message.error(err.message || '处理失败，请重试');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleImport = async () => {
    if (!correctedData?.testcases) return;

    setImporting(true);

    try {
      // 批量创建测试用例
      const response = await fetch('/api/v1/testcases/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          testcases: correctedData.testcases,
          project_id: projectId,
        }),
      });

      const result = await response.json();

      if (result.code === 0) {
        setCurrentStep(2);
        setTimeout(() => {
          onSuccess(result.data.count);
        }, 1500);
      } else {
        throw new Error(result.message || '批量导入失败');
      }
    } catch (err: any) {
      console.error('批量导入失败:', err);
      message.error(err.message || '批量导入失败');
    } finally {
      setImporting(false);
    }
  };

  const loadSampleJson = () => {
    const sample = [
      {
        name: '用户登录测试',
        description: '验证用户登录功能',
        priority: 'P1',
        steps: ['打开登录页面', '输入用户名', '输入密码', '点击登录按钮'],
      },
      {
        name: '搜索功能测试',
        description: '验证搜索功能正常',
        priority: 'P2',
        steps: ['输入搜索关键词', '点击搜索按钮', '验证搜索结果'],
      },
    ];
    setJsonInput(JSON.stringify(sample, null, 2));
    setJsonError(null);
  };

  const renderUploadStep = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Paragraph type="secondary">
        上传JSON格式的测试用例数据，AI将自动修正格式并准备批量导入。
      </Paragraph>

      <Card title="支持的数据格式" size="small">
        <Paragraph>
          <Text code>
            {JSON.stringify([
              { name: '测试用例1', description: '描述', steps: ['步骤1', '步骤2'] },
              { name: '测试用例2', description: '描述', steps: ['步骤1', '步骤2'] },
            ], null, 2)}
          </Text>
        </Paragraph>
      </Card>

      <Dragger
        accept=".json"
        showUploadList={false}
        beforeUpload={(file) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const content = e.target?.result as string;
            setJsonInput(content);
          };
          reader.readAsText(file);
          return false;
        }}
      >
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽JSON文件到此区域上传</p>
        <p className="ant-upload-hint">支持单个或批量测试用例JSON文件</p>
      </Dragger>

      <Divider orientation={"left" as any}>或直接粘贴JSON</Divider>

      <TextArea
        rows={12}
        placeholder={`[
  {
    "name": "测试用例名称",
    "description": "测试用例描述",
    "priority": "P1",
    "steps": ["步骤1", "步骤2"]
  }
]`}
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
        <Space>
          <Button
            onClick={() => handleAnalyze(true)}
            disabled={!jsonInput.trim() || analyzing}
            loading={analyzing}
          >
            跳过AI修正
          </Button>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={() => handleAnalyze(false)}
            disabled={!jsonInput.trim() || analyzing}
            loading={analyzing}
          >
            {analyzing ? 'AI修正中...' : 'AI修正格式'}
          </Button>
        </Space>
      </Space>
    </Space>
  );

  const renderCorrectStep = () => {
    if (!correctedData) return null;

    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Alert
          message="AI修正完成"
          description="JSON格式已优化，可以导入的测试用例"
          type="success"
          showIcon
        />

        <Row gutter={16}>
          <Col span={8}>
            <Card>
              <Statistic
                title="测试用例数量"
                value={correctedData.testcases?.length || 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="修正的字段"
                value={correctedData.corrections?.length || 0}
                suffix="个"
                prefix={<DiffOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="需要人工确认"
                value={correctedData.needs_review || 0}
                suffix="个"
                valueStyle={{ color: correctedData.needs_review > 0 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>

        {correctedData.corrections && correctedData.corrections.length > 0 && (
          <Card title="AI修正说明" size="small">
            <List
              size="small"
              dataSource={correctedData.corrections}
              renderItem={(correction: any, index: number) => (
                <List.Item key={index}>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Tag color="blue">{correction.field || '未知字段'}</Tag>
                        <Text>{correction.issue || '修正说明'}</Text>
                      </Space>
                    }
                    description={
                      <Space>
                        <Text type="danger">原值: {String(correction.old_value || correction.old_value)}</Text>
                        <Text type="success">→</Text>
                        <Text type="success">新值: {String(correction.new_value || correction.new_value)}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        <Card title="修正后的测试用例" size="small">
          <List
            dataSource={correctedData.testcases || []}
            renderItem={(testcase: any, index: number) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space>
                      <strong>{index + 1}. {testcase.case_name || testcase.name || '未命名'}</strong>
                      {testcase.needs_review && (
                        <Tag color="warning">需要确认</Tag>
                      )}
                    </Space>
                  }
                  description={
                    testcase.description ||
                    (testcase.flow?.name && `包含Flow: ${testcase.flow?.name}`)
                  }
                />
                <div>
                  {testcase.flow?.step?.length || testcase.steps?.length || 0} 个步骤
                </div>
              </List.Item>
            )}
          />
        </Card>

        {correctedData.warnings && correctedData.warnings.length > 0 && (
          <Alert
            message="注意事项"
            description={
              <ul>
                {correctedData.warnings.map((warning: string, i: number) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            }
            type="warning"
            showIcon
          />
        )}
      </Space>
    );
  };

  const renderConfirmStep = () => (
    <div style={{ textAlign: 'center', padding: '40px 0' }}>
      <CheckOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 16 }} />
      <Title level={3}>批量导入成功！</Title>
      <Paragraph type="secondary">
        成功导入 {correctedData?.testcases?.length || 0} 个测试用例
      </Paragraph>
    </div>
  );

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderUploadStep();
      case 1:
        return renderCorrectStep();
      case 2:
        return renderConfirmStep();
      default:
        return null;
    }
  };

  return (
    <Modal
      title={
        <Space>
          <FileTextOutlined />
          批量导入测试用例 - AI辅助
        </Space>
      }
      open={true}
      onCancel={onCancel}
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

        <Spin spinning={analyzing || importing} tip={analyzing ? 'AI分析中...' : '导入中...'}>
          {renderStepContent()}
        </Spin>

        <Divider />

        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
          {currentStep === 0 && (
            <>
              <Button onClick={onCancel}>取消</Button>
            </>
          )}
          {currentStep === 1 && (
            <>
              <Button icon={<ArrowLeftOutlined />} onClick={() => setCurrentStep(0)}>
                返回修改
              </Button>
              <Button
                type="primary"
                icon={<CheckOutlined />}
                onClick={handleImport}
                loading={importing}
              >
                确认导入
              </Button>
            </>
          )}
          {currentStep === 2 && (
            <Button type="primary" onClick={onCancel}>
              完成
            </Button>
          )}
        </Space>
      </Space>
    </Modal>
  );
};

export default BatchImportWizard;
