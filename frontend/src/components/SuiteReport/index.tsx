import React, { useState, useEffect } from 'react';
import {
  Modal,
  List,
  Tag,
  Progress,
  Card,
  Tabs,
  Timeline,
  Empty,
  Spin,
  Row,
  Col,
  Image,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

interface SuiteReportProps {
  visible: boolean;
  taskId: string;
  suiteName: string;
  onClose: () => void;
}

const SuiteReport: React.FC<SuiteReportProps> = ({
  visible,
  taskId,
  suiteName,
  onClose,
}) => {
  const [logs, setLogs] = useState<any[]>([]);
  const [screenshots, setScreenshots] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (visible && taskId) {
      fetchLogs();
      fetchScreenshots();
    }
  }, [visible, taskId]);

  const fetchScreenshots = async () => {
    try {
      const response = await api.get(`/runs/${taskId}/screenshots`);
      const data = response.data;
      if (data?.code === 0 && data?.data?.screenshots) {
        setScreenshots(data.data.screenshots);
      }
    } catch (error) {
      console.error('获取截图失败:', error);
    }
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/runs/${taskId}/logs`);
      const data = response.data;

      // 从 SSE 数据中提取日志
      const logEntries = [];
      if (data?.data?.logs) {
        logEntries.push(...data.data.logs);
      }

      setLogs(logEntries);
    } catch (error) {
      console.error('获取日志失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 解析日志，提取用例执行信息
  const parseTestcases = () => {
    const testcases: Map<number, any> = new Map();
    const testcaseLogs: Map<number, any[]> = new Map();

    logs.forEach((log) => {
      if (log.testcase_id) {
        const tcId = log.testcase_id;

        if (!testcases.has(tcId)) {
          testcases.set(tcId, {
            id: tcId,
            name: log.testcase_name || `用例 ${tcId}`,
            result: log.testcase_result || 'running',
            logs: [],
          });
        }

        // 收集该用例的日志
        if (!testcaseLogs.has(tcId)) {
          testcaseLogs.set(tcId, []);
        }
        testcaseLogs.get(tcId).push(log);
      }
    });

    return Array.from(testcases.values()).map((tc) => ({
      ...tc,
      logs: testcaseLogs.get(tc.id) || [],
    }));
  };

  const testcases = parseTestcases();

  const total = testcases.length;
  const passed = testcases.filter((tc) => tc.result === 'passed').length;
  const failed = testcases.filter((tc) => tc.result === 'failed').length;
  const skipped = testcases.filter((tc) => tc.result === 'skipped').length;
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;

  const getStatusIcon = (result: string) => {
    switch (result) {
      case 'passed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'skipped':
        return <MinusCircleOutlined style={{ color: '#8c8c8c' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const getStatusTag = (result: string) => {
    switch (result) {
      case 'passed':
        return <Tag icon={<CheckCircleOutlined />} color="success">通过</Tag>;
      case 'failed':
        return <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>;
      case 'skipped':
        return <Tag icon={<MinusCircleOutlined />} color="default">跳过</Tag>;
      default:
        return <Tag icon={<ClockCircleOutlined />} color="processing">执行中</Tag>;
    }
  };

  return (
    <Modal
      title={`套件执行报告 - ${suiteName}`}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1000}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          {/* 统计信息 */}
          <Card style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Card>
                  <Progress
                    type="circle"
                    percent={passRate}
                    format={(percent) => `${percent}%`}
                    strokeColor={{
                      '0%': '#ff4d4f',
                      '50%': '#ffc53d',
                      '100%': '#52c41a',
                    }}
                  />
                  <div style={{ textAlign: 'center', marginTop: 8 }}>通过率</div>
                </Card>
              </Col>
              <Col span={18}>
                <Row gutter={16}>
                  <Col span={6}>
                    <Card>
                      <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                        {total}
                      </div>
                      <div style={{ color: '#8c8c8c' }}>总用例数</div>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                        {passed}
                      </div>
                      <div style={{ color: '#8c8c8c' }}>通过</div>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
                        {failed}
                      </div>
                      <div style={{ color: '#8c8c8c' }}>失败</div>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <div style={{ fontSize: 24, fontWeight: 'bold', color: '#8c8c8c' }}>
                        {skipped}
                      </div>
                      <div style={{ color: '#8c8c8c' }}>跳过</div>
                    </Card>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Card>

          {/* 失败截图 */}
          {screenshots.length > 0 && (
            <Card title="失败截图" style={{ marginBottom: 16 }}>
              <Row gutter={[16, 16]}>
                {screenshots.map((screenshot, index) => (
                  <Col span={8} key={index}>
                    <Card
                      size="small"
                      hoverable
                      onClick={() => window.open(`http://localhost:8000/api/v1/screenshots/${screenshot.filename}`, '_blank')}
                    >
                      <div style={{ textAlign: 'center' }}>
                        <Image
                          width={200}
                          src={`http://localhost:8000/api/v1/screenshots/${screenshot.filename}`}
                          preview={{
                            src: `http://localhost:8000/api/v1/screenshots/${screenshot.filename}`,
                          }}
                        />
                        <div style={{ marginTop: 8, fontSize: 12 }}>
                          <div><strong>步骤:</strong> {screenshot.step_name}</div>
                          <div style={{ color: '#8c8c8c' }}>{screenshot.timestamp}</div>
                        </div>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>
          )}

          {/* 用例列表 */}
          <Card title="用例执行详情">
            {testcases.length === 0 ? (
              <Empty description="暂无用例数据" />
            ) : (
              <List
                dataSource={testcases}
                renderItem={(testcase) => (
                  <List.Item
                    actions={[
                      getStatusTag(testcase.result),
                    ]}
                  >
                    <List.Item.Meta
                      avatar={getStatusIcon(testcase.result)}
                      title={testcase.name}
                      description={
                        <Tabs
                          defaultActiveKey="summary"
                          items={[
                            {
                              key: 'summary',
                              label: '概要',
                              children: (
                                <div>
                                  <p>用例ID: {testcase.id}</p>
                                  <p>状态: {testcase.result}</p>
                                  <p>日志条数: {testcase.logs.length}</p>
                                </div>
                              ),
                            },
                            {
                              key: 'logs',
                              label: `日志 (${testcase.logs.length})`,
                              children: testcase.logs.length === 0 ? (
                                <Empty description="暂无日志" />
                              ) : (
                                <Timeline>
                                  {testcase.logs.map((log: any, index: number) => (
                                    <Timeline.Item
                                      key={index}
                                      color={
                                        log.level === 'ERROR' ? 'red' :
                                        log.level === 'WARNING' ? 'orange' :
                                        log.level === 'INFO' ? 'blue' : 'gray'
                                      }
                                    >
                                      <Tag color={
                                        log.level === 'ERROR' ? 'error' :
                                        log.level === 'WARNING' ? 'warning' :
                                        log.level === 'INFO' ? 'blue' : 'default'
                                      }>
                                        {log.level}
                                      </Tag>
                                      <span style={{ marginLeft: 8 }}>{log.message}</span>
                                    </Timeline.Item>
                                  ))}
                                </Timeline>
                              ),
                            },
                          ]}
                        />
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </>
      )}
    </Modal>
  );
};

export default SuiteReport;
