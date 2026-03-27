import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const Tags: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Result
      status="info"
      title="标签管理"
      subTitle="此页面正在开发中"
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回控制台
        </Button>
      }
    />
  );
};

export default Tags;
