/**
 * 侧边抽屉选择器组件
 * 替代传统下拉框，提供更好的用户体验
 */
import React, { useState, useEffect, useMemo } from 'react';
import {
  Drawer,
  List,
  Input,
  Tag,
  Button,
  Space,
  Typography,
  Empty,
  Spin,
  Checkbox,
} from 'antd';
import {
  SearchOutlined,
  CheckOutlined,
  CloseOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

export interface DrawerSelectorOption {
  value: string | number;
  label: string;
  description?: string;
  disabled?: boolean;
  extra?: React.ReactNode;
  [key: string]: any;
}

export interface DrawerSelectorProps {
  options: DrawerSelectorOption[];
  loading?: boolean;
  searchable?: boolean;
  placeholder?: string;
  value?: string | number | Array<string | number> | null;
  onChange?: (value: any) => void;
  multiple?: boolean;
  disabled?: boolean;
  title?: string;
  drawerWidth?: number;
  placement?: 'left' | 'right';
  trigger?: React.ReactNode;
  renderExtra?: (option: DrawerSelectorOption) => React.ReactNode;
  selectedColor?: string;
  allowClear?: boolean;
  onSearch?: (keyword: string) => void;
}

const DrawerSelector: React.FC<DrawerSelectorProps> = ({
  options = [],
  loading = false,
  searchable = true,
  placeholder = '请选择',
  value,
  onChange,
  multiple = false,
  disabled = false,
  title = '请选择',
  drawerWidth = 480,
  placement = 'right',
  trigger,
  renderExtra,
  selectedColor = 'blue',
  allowClear = true,
  onSearch,
}) => {
  const [visible, setVisible] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [internalValue, setInternalValue] = useState(value);

  useEffect(() => { setInternalValue(value); }, [value]);

  const handleOpen = () => {
    if (!disabled) { setVisible(true); setSearchKeyword(''); }
  };

  const handleClose = () => {
    setVisible(false);
    setSearchKeyword('');
  };

  const handleSelect = (option: DrawerSelectorOption) => {
    if (option.disabled) return;
    if (multiple) {
      const currentValue = internalValue || [];
      const newValue = currentValue.includes(option.value)
        ? currentValue.filter((v: any) => v !== option.value)
        : [...currentValue, option.value];
      setInternalValue(newValue);
      onChange?.(newValue);
    } else {
      setInternalValue(option.value);
      onChange?.(option.value);
      handleClose();
    }
  };

  const filteredOptions = useMemo(() => {
    if (!searchKeyword) return options;
    const keyword = searchKeyword.toLowerCase();
    return options.filter(opt =>
      opt.label.toLowerCase().includes(keyword) ||
      opt.description?.toLowerCase().includes(keyword)
    );
  }, [options, searchKeyword]);

  const isSelected = (optionValue: any) => {
    if (multiple) {
      const values = internalValue || [];
      return values.includes(optionValue);
    }
    return internalValue === optionValue;
  };

  const selectedLabel = useMemo(() => {
    if (!internalValue) return placeholder;
    if (multiple) {
      const count = (internalValue as any[]).length;
      return count > 0 ? <>已选 {count} 项</> : placeholder;
    }
    const opt = options.find(o => o.value === internalValue);
    return opt?.label || placeholder;
  }, [internalValue, options, multiple, placeholder]);

  return (
    <>
      <Button onClick={handleOpen} disabled={disabled} style={{ minWidth: 200 }}>
        {selectedLabel}
      </Button>
      <Drawer
        title={title}
        placement={placement}
        width={drawerWidth}
        open={visible}
        onClose={handleClose}
        destroyOnClose
      >
        {searchable && (
          <Input
            placeholder="搜索..."
            value={searchKeyword}
            onChange={(e) => { setSearchKeyword(e.target.value); onSearch?.(e.target.value); }}
            prefix={<SearchOutlined />}
            style={{ margin: 16 }}
          />
        )}
        <div style={{ height: 'calc(100vh - 150px)', overflow: 'auto' }}>
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center' }}><Spin /></div>
          ) : filteredOptions.length === 0 ? (
            <Empty style={{ marginTop: 60 }} />
          ) : (
            <List
              dataSource={filteredOptions}
              renderItem={(option: DrawerSelectorOption) => {
                const selected = isSelected(option.value);
                return (
                  <List.Item
                    key={option.value}
                    style={{
                      padding: '12px 16px',
                      cursor: option.disabled ? 'not-allowed' : 'pointer',
                      backgroundColor: selected ? '#f0f0f0' : 'transparent',
                    }}
                    onClick={() => handleSelect(option)}
                  >
                    <Space style={{ width: '100%' }}>
                      {multiple && <Checkbox checked={selected} disabled={option.disabled} />}
                      {!multiple && selected && <CheckOutlined style={{ color: selectedColor }} />}
                      <div>
                        <div>{option.label}</div>
                        {option.description && (
                          <Text type="secondary" style={{ fontSize: 12 }}>{option.description}</Text>
                        )}
                      </div>
                    </Space>
                  </List.Item>
                );
              }}
            />
          )}
        </div>
      </Drawer>
    </>
  );
};

export default DrawerSelector;
