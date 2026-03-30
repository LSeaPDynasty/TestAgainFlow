import React, { useState } from 'react';
import { Button, Space, Typography, message } from 'antd';
import { ThunderboltOutlined, CheckOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

interface AIDescriptionProps {
  type: 'step' | 'flow' | 'testcase';
  data: any;
  onDescriptionGenerated: (description: string) => void;
  style?: React.CSSProperties;
  disabled?: boolean;
}

const AIDescription: React.FC<AIDescriptionProps> = ({
  type,
  data,
  onDescriptionGenerated,
  style,
  disabled = false,
}) => {
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  const handleGenerate = async () => {
    if (disabled) {
      message.warning('请先填写必要信息');
      return;
    }

    setLoading(true);
    try {
      let endpoint = '';
      let requestData: any = {};

      if (type === 'step') {
        endpoint = '/ai/steps/generate-description';
        requestData = {
          step_name: data.step_name || '',
          action_type: data.action_type || '',
          element_name: data.element_name,
          element_description: data.element_description,
        };
      } else if (type === 'flow') {
        endpoint = '/ai/flows/generate-description';
        requestData = {
          flow_name: data.flow_name || '',
          flow_type: data.flow_type || 'standard',
          step_names: data.step_names || [],
          purpose: data.purpose,
        };
      } else if (type === 'testcase') {
        endpoint = '/ai/testcases/generate-description';
        requestData = {
          testcase_name: data.testcase_name || '',
          flow_names: data.flow_names || [],
          priority: data.priority || 'P1',
          tags: data.tags || [],
        };
      }

      const response = await api.post(endpoint, requestData);
      const description = response.data.data.description;
      
      onDescriptionGenerated(description);
      setGenerated(true);
      message.success('AI描述生成成功');

      setTimeout(() => setGenerated(false), 3000);
    } catch (error: any) {
      console.error('AI生成失败:', error);
      message.error(error.response?.data?.message || 'AI服务暂时不可用');
    } finally {
      setLoading(false);
    }
  };

  const getButtonText = () => {
    if (type === 'step') return 'AI生成步骤描述';
    if (type === 'flow') return 'AI生成流程描述';
    if (type === 'testcase') return 'AI生成用例描述';
    return 'AI生成描述';
  };

  const getTipText = () => {
    if (type === 'step') return '💡 AI会根据操作类型和元素信息生成步骤描述';
    if (type === 'flow') return '💡 AI会根据步骤列表和流程类型生成流程描述';
    if (type === 'testcase') return '💡 AI会根据流程和优先级生成用例描述';
    return '💡 AI会智能生成描述';
  };

  return (
    <div style={style}>
      <Button
        type="dashed"
        icon={generated ? <CheckOutlined /> : <ThunderboltOutlined />}
        onClick={handleGenerate}
        loading={loading}
        disabled={disabled}
        block
        style={{
          borderColor: generated ? '#52c41a' : '#1890ff',
          color: generated ? '#52c41a' : '#1890ff',
        }}
      >
        {loading ? 'AI生成中...' : generated ? '已生成' : getButtonText()}
      </Button>
      <div style={{ marginTop: 8 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {getTipText()}
        </Text>
      </div>
    </div>
  );
};

export default AIDescription;
