import React from 'react';
import { Drawer } from 'antd';

interface RightDrawerProps {
  visible: boolean;
  content: React.ReactNode | null;
  onClose: () => void;
}

const RightDrawer: React.FC<RightDrawerProps> = ({ visible, content, onClose }) => {
  return (
    <Drawer
      title="详情"
      placement="right"
      size="large"
      open={visible}
      onClose={onClose}
      styles={{
        body: { padding: '24px' },
      }}
    >
      {content}
    </Drawer>
  );
};

export default RightDrawer;
