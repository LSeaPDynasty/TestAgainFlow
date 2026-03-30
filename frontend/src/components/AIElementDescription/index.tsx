import React, { useState } from 'react';
import { Button, Space, Typography, Alert, Spin } from 'antd';
import { ThunderboltOutlined, CheckOutlined } from '@ant-design/icons';
import { message } from 'antd';

const { Text } = Typography;

interface AIElementDescriptionProps {
  elementName: string;
  screenName: string;
  locators: any[];
  onDescriptionGenerated: (description: string) => void;
  style?: React.CSSProperties;
}

const AIElementDescription: React.FC<AIElementDescriptionProps> = ({
  elementName,
  screenName,
  locators,
  onDescriptionGenerated,
  style,
}) => {
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  const handleGenerate = async () => {
    if (!elementName || !screenName) {
      message.warning('请先填写元素名称和所属界面');
      return;
    }

    if (!locators || locators.length === 0) {
      message.warning('请先添加至少一个定位符');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/ai/elements/generate-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          element_name: elementName,
          screen_name: screenName,
          locators: locators,
        }),
      });

      const data = await response.json();

      if (data.code === 0) {
        const description = data.data.description;
        onDescriptionGenerated(description);
        setGenerated(true);
        message.success('AI描述生成成功');

        // 3秒后重置状态
        setTimeout(() => setGenerated(false), 3000);
      } else {
        message.error(data.message || '生成失败');
      }
    } catch (error: any) {
      console.error('AI生成失败:', error);
      message.error(error.message || 'AI服务暂时不可用');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={style}>
      <Button
        type="dashed"
        icon={generated ? <CheckOutlined /> : <ThunderboltOutlined />}
        onClick={handleGenerate}
        loading={loading}
        block
        style={{
          borderColor: generated ? '#52c41a' : '#1890ff',
          color: generated ? '#52c41a' : '#1890ff',
        }}
      >
        {loading ? 'AI生成中...' : generated ? '已生成' : 'AI生成描述'}
      </Button>
      <div style={{ marginTop: 8 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          💡 AI会根据元素名称、界面和定位符生成规范的描述
        </Text>
      </div>
    </div>
  );
};

export default AIElementDescription;
