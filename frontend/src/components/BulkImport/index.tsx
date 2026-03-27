import React, { useState } from 'react';
import {
  Modal,
  Upload,
  Button,
  Space,
  Alert,
  Descriptions,
  Tag,
  Progress,
  Checkbox,
  Radio,
  Typography,
  Divider,
  Card,
  Row,
  Col,
  message,
  Collapse,
  Statistic,
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  FileOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import {
  uploadImportFile,
  downloadJsonTemplate,
  downloadYamlTemplate,
  downloadElementsOnlyTemplate,
} from '../../services/import';

const { Text, Paragraph, Title } = Typography;
const { Panel } = Collapse;

interface BulkImportProps {
  visible: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

interface ImportResult {
  success: boolean;
  message: string;
  created_screens: number;
  created_elements: number;
  skipped_screens: string[];
  skipped_elements: string[];
  errors: string[];
}

const BulkImport: React.FC<BulkImportProps> = ({ visible, onClose, onSuccess }) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [skipExisting, setSkipExisting] = useState(true);
  const [createScreens, setCreateScreens] = useState(true);
  const [importMode, setImportMode] = useState<'file' | 'template'>('file');

  // 处理文件上传
  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请选择要导入的文件');
      return;
    }

    const file = fileList[0].originFileObj;
    if (!file) {
      message.warning('文件无效');
      return;
    }

    setImporting(true);
    setImportResult(null);

    try {
      const response = await uploadImportFile(file, {
        skip_existing: skipExisting,
        create_screens: createScreens,
      });

      const result = response.data.data;
      setImportResult(result);

      if (result.success) {
        message.success('导入成功！');
        if (onSuccess) {
          onSuccess();
        }
      } else {
        message.warning(`导入完成，但有 ${result.errors.length} 个错误`);
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '导入失败');
    } finally {
      setImporting(false);
    }
  };

  // 下载模板
  const handleDownloadTemplate = async (type: 'json' | 'yaml' | 'elements-only') => {
    try {
      let downloadFn;
      let filename;

      switch (type) {
        case 'json':
          downloadFn = downloadJsonTemplate;
          filename = 'import_template.json';
          break;
        case 'yaml':
          downloadFn = downloadYamlTemplate;
          filename = 'import_template.yaml';
          break;
        case 'elements-only':
          downloadFn = downloadElementsOnlyTemplate;
          filename = 'elements_only_template.json';
          break;
      }

      const response = await downloadFn();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success(`模板下载成功: ${filename}`);
    } catch (error) {
      message.error('模板下载失败');
    }
  };

  // 重置状态
  const handleClose = () => {
    setFileList([]);
    setImportResult(null);
    onClose();
  };

  return (
    <Modal
      title="批量导入"
      open={visible}
      onCancel={handleClose}
      width={800}
      footer={[
        <Button key="cancel" onClick={handleClose} disabled={importing}>
          关闭
        </Button>,
        <Button
          key="import"
          type="primary"
          icon={<UploadOutlined />}
          loading={importing}
          onClick={handleUpload}
          disabled={fileList.length === 0}
        >
          开始导入
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 使用说明 */}
        <Alert
          message="导入说明"
          description={
            <div>
              <Paragraph>
                支持 JSON 和 YAML 格式的批量导入。可以同时导入界面和元素，或将元素导入到已存在的界面。
              </Paragraph>
              <Space>
                <Text strong>支持格式：</Text>
                <Tag color="blue">.json</Tag>
                <Tag color="green">.yaml</Tag>
                <Tag color="green">.yml</Tag>
              </Space>
            </div>
          }
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
        />

        {/* 模板下载 */}
        <Card size="small" title="📥 下载模板">
          <Row gutter={16}>
            <Col span={8}>
              <Button
                block
                icon={<CodeOutlined />}
                onClick={() => handleDownloadTemplate('json')}
              >
                JSON模板
              </Button>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                完整模板（界面+元素）
              </Text>
            </Col>
            <Col span={8}>
              <Button
                block
                icon={<FileOutlined />}
                onClick={() => handleDownloadTemplate('yaml')}
              >
                YAML模板
              </Button>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                完整模板（界面+元素）
              </Text>
            </Col>
            <Col span={8}>
              <Button
                block
                icon={<FileTextOutlined />}
                onClick={() => handleDownloadTemplate('elements-only')}
              >
                元素模板
              </Button>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                仅元素（导入到已有界面）
              </Text>
            </Col>
          </Row>
        </Card>

        {/* 导入选项 */}
        <Card size="small" title="⚙️ 导入选项">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Checkbox checked={skipExisting} onChange={(e) => setSkipExisting(e.target.checked)}>
              跳过已存在的界面和元素
            </Checkbox>
            <Checkbox checked={createScreens} onChange={(e) => setCreateScreens(e.target.checked)}>
              自动创建不存在的界面
            </Checkbox>
          </Space>
        </Card>

        {/* 文件上传 */}
        <Card size="small" title="📤 上传文件">
          <Upload.Dragger
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList)}
            beforeUpload={() => false}  // 阻止自动上传
            accept=".json,.yaml,.yml"
            maxCount={1}
            disabled={importing}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持 .json、.yaml、.yml 格式，单个文件不超过 5MB
            </p>
          </Upload.Dragger>
        </Card>

        {/* 导入结果 */}
        {importResult && (
          <Card
            size="small"
            title={
              <Space>
                {importResult.success ? (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                ) : (
                  <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                )}
                <span>导入结果</span>
              </Space>
            }
          >
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="创建界面"
                  value={importResult.created_screens}
                  valueStyle={{ color: '#3f8600' }}
                  suffix="个"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="创建元素"
                  value={importResult.created_elements}
                  valueStyle={{ color: '#3f8600' }}
                  suffix="个"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="跳过项目"
                  value={importResult.skipped_screens.length + importResult.skipped_elements.length}
                  valueStyle={{ color: '#faad14' }}
                  suffix="个"
                />
              </Col>
            </Row>

            <Divider />

            <Collapse ghost>
              {importResult.skipped_screens.length > 0 && (
                <Panel header={`跳过的界面 (${importResult.skipped_screens.length})`} key="skipped_screens">
                  <Space wrap>
                    {importResult.skipped_screens.map((name) => (
                      <Tag key={name} color="default">
                        {name}
                      </Tag>
                    ))}
                  </Space>
                </Panel>
              )}
              {importResult.skipped_elements.length > 0 && (
                <Panel header={`跳过的元素 (${importResult.skipped_elements.length})`} key="skipped_elements">
                  <Space wrap>
                    {importResult.skipped_elements.map((name) => (
                      <Tag key={name} color="default">
                        {name}
                      </Tag>
                    ))}
                  </Space>
                </Panel>
              )}
              {importResult.errors.length > 0 && (
                <Panel header={`错误信息 (${importResult.errors.length})`} key="errors">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {importResult.errors.map((error, index) => (
                      <Alert
                        key={index}
                        message={error}
                        type="error"
                        showIcon
                      />
                    ))}
                  </Space>
                </Panel>
              )}
            </Collapse>
          </Card>
        )}
      </Space>
    </Modal>
  );
};

export default BulkImport;
