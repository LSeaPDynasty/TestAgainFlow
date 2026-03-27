import React, { useState, useEffect } from 'react';
import {
  Button,
  Space,
  Select,
  Switch,
  Modal,
  Form,
  Input,
  InputNumber,
  Tag,
  Popconfirm,
  message,
  Collapse,
  Alert,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  DragOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { getFlows, getFlow } from '../../services/flow';
import { getSteps, getStep } from '../../services/step';
import { getElement } from '../../services/element';
import { useProject } from '../../contexts/ProjectContext';

// 本地类型定义，避免导入问题
export interface TestcaseItem {
  id: number;
  testcase_id: number;
  item_type: 'flow' | 'step';
  flow_id?: number;
  step_id?: number;
  order_index: number;
  enabled: boolean;
  continue_on_error?: boolean;
  params?: Record<string, any>;
  flow_name?: string;
  step_name?: string;
  step_action_type?: string;
  step_action_value?: string;  // Step 的 action_value
  flow_params?: Record<string, any>;  // Flow 的默认参数
  step_params?: string[];  // Step 中提取的参数名列表
  detected_params?: string[];  // 从 Element 自动识别的参数名列表（不管有没有值）
  created_at: string;
  updated_at: string;
}

interface TestcaseItemsEditorProps {
  items: TestcaseItem[];
  onChange: (items: TestcaseItem[]) => void;
  testcaseId?: number;
}

const TestcaseItemsEditor: React.FC<TestcaseItemsEditorProps> = ({ items: initialItems, onChange, testcaseId }) => {
  // 清理函数：确保 params 中的所有值都是字符串
  const cleanItemParams = (item: TestcaseItem): TestcaseItem => {
    if (!item.params || typeof item.params !== 'object') {
      return item;
    }

    const cleanedParams: Record<string, string> = {};
    Object.entries(item.params).forEach(([key, value]) => {
      if (typeof value === 'object' && value !== null) {
        cleanedParams[key] = JSON.stringify(value);
      } else {
        cleanedParams[key] = String(value ?? '');
      }
    });

    return {
      ...item,
      params: cleanedParams,
    };
  };

  // 使用内部状态管理 items，确保 UI 实时更新
  const [items, setItems] = useState<TestcaseItem[]>(
    (initialItems || []).map(cleanItemParams)
  );

  // 当外部传入的 initialItems 变化时，同步更新内部状态
  useEffect(() => {
    setItems((initialItems || []).map(cleanItemParams));
  }, [initialItems]);

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | -1>(-1);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [selectedStepDetail, setSelectedStepDetail] = useState<any>(null);
  const [manualParams, setManualParams] = useState<string[]>([]);
  const [form] = Form.useForm();
  const { selectedProjectId } = useProject();

  const { data: flowsResp } = useQuery({
    queryKey: ['flows-for-items-editor', selectedProjectId],
    queryFn: () => getFlows({ page: 1, page_size: 1000, project_id: selectedProjectId || undefined }),
    enabled: addModalOpen || editingIndex >= 0,
  });

  const { data: stepsResp } = useQuery({
    queryKey: ['steps-for-items-editor', selectedProjectId],
    queryFn: () => getSteps({ page: 1, page_size: 1000, project_id: selectedProjectId || undefined }),
    enabled: addModalOpen || editingIndex >= 0,
  });

  const flowOptions =
    (flowsResp?.data?.data?.items || []).map((f: any) => ({
      label: f.name,
      value: f.id,
    })) || [];

  const stepOptions =
    (stepsResp?.data?.data?.items || []).map((s: any) => ({
      label: `${s.name} (${s.action_type})`,
      value: s.id,
    })) || [];

  const handleAdd = () => {
    setEditingIndex(-1);
    setSelectedStepDetail(null);
    setManualParams([]);
    form.resetFields();
    form.setFieldsValue({
      item_type: 'flow',
      flow_id: undefined,
      step_id: undefined,
      order_index: items.length + 1,
      enabled: true,
      continue_on_error: false,
    });
    setAddModalOpen(true);
  };

  const handleEdit = async (index: number) => {
    const item = items[index];
    setEditingIndex(index);

    // 先重置表单，清除旧值
    form.resetFields();

    // 立即设置 params 为空对象，防止残留值
    form.setFieldValue('params', {});

    setSelectedStepDetail(null);
    setManualParams([]);

    // 如果是 Step，获取详情并自动识别 Element 参数
    if (item.item_type === 'step' && item.step_id) {
      try {
        const stepResp = await getStep(item.step_id);
        const stepDetail = stepResp?.data?.data;
        setSelectedStepDetail(stepDetail);

        // 尝试从 Element 的 locators 自动提取参数
        if (stepDetail?.element_id) {
          try {
            const elementResp = await getElement(stepDetail.element_id);
            const element = elementResp?.data?.data;
            if (element?.locators && Array.isArray(element.locators)) {
              // 从所有 locator 的 value 中提取参数
              const allParams = new Set<string>();
              element.locators.forEach((locator: any) => {
                if (locator.value) {
                  const params = extractTemplateParams(locator.value);
                  params.forEach(param => allParams.add(param));
                }
              });

              if (allParams.size > 0) {
                setManualParams(Array.from(allParams));
              } else {
                // 如果没有从 Element 识别到参数，但 item 中有 detected_params，则使用它
                if (item.detected_params && item.detected_params.length > 0) {
                  setManualParams([...item.detected_params]);
                }
              }
            }
          } catch (e) {
            console.error('Failed to fetch element details:', e);
            // 如果获取失败，但 item 中有 detected_params，则使用它
            if (item.detected_params && item.detected_params.length > 0) {
              setManualParams([...item.detected_params]);
            }
          }
        } else if (item.detected_params && item.detected_params.length > 0) {
          // 如果没有 element_id，但 item 中有 detected_params，则使用它
          setManualParams([...item.detected_params]);
        }
      } catch (e) {
        console.error('Failed to fetch step details:', e);
        setSelectedStepDetail(null);
        // 失败时也尝试使用已有的 detected_params
        if (item.detected_params && item.detected_params.length > 0) {
          setManualParams([...item.detected_params]);
        }
      }
    }

    // 确保 params 中的所有值都是字符串
    const safeParams = item.params || {};
    const stringifiedParams: Record<string, string> = {};
    Object.entries(safeParams).forEach(([key, value]) => {
      stringifiedParams[key] = typeof value === 'object' ? JSON.stringify(value) : String(value || '');
    });

    // 设置表单值
    form.setFieldsValue({
      item_type: item.item_type,
      flow_id: item.flow_id,
      step_id: item.step_id,
      order_index: item.order_index,
      enabled: item.enabled,
      continue_on_error: item.continue_on_error || false,
      params: stringifiedParams,
    });

    setAddModalOpen(true);
  };

  const handleDelete = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    // 重新排序
    newItems.forEach((item, i) => {
      item.order_index = i + 1;
    });
    setItems(newItems);
    onChange(newItems);
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const newItems = [...items];
    [newItems[index - 1], newItems[index]] = [newItems[index], newItems[index - 1]];
    // 更新 order_index
    newItems.forEach((item, i) => {
      item.order_index = i + 1;
    });
    setItems(newItems);
    onChange(newItems);
  };

  const handleMoveDown = (index: number) => {
    if (index === items.length - 1) return;
    const newItems = [...items];
    [newItems[index], newItems[index + 1]] = [newItems[index + 1], newItems[index]];
    // 更新 order_index
    newItems.forEach((item, i) => {
      item.order_index = i + 1;
    });
    setItems(newItems);
    onChange(newItems);
  };

  const handleToggleEnabled = (index: number) => {
    const newItems = [...items];
    newItems[index].enabled = !newItems[index].enabled;
    setItems(newItems);
    onChange(newItems);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const { item_type, flow_id, step_id, order_index, enabled, continue_on_error, params } = values;

      // 验证：flow 类型必须有 flow_id，step 类型必须有 step_id
      if (item_type === 'flow' && !flow_id) {
        message.error('Flow 类型必须选择 Flow');
        return;
      }
      if (item_type === 'step' && !step_id) {
        message.error('Step 类型必须选择 Step');
        return;
      }

      // 查找 flow_name 和 step_name
      const flows = flowsResp?.data?.data?.items || [];
      const steps = stepsResp?.data?.data?.items || [];

      const selectedFlow = flows.find((f: any) => f.id === flow_id);
      const selectedStep = steps.find((s: any) => s.id === step_id);

      // 获取 Flow 或 Step 的详细信息（包括参数定义）
      let flowParams: Record<string, any> = {};
      let stepParams: string[] = [];
      let stepActionValue = '';

      if (item_type === 'flow' && flow_id) {
        try {
          const flowDetailResp = await getFlow(flow_id);
          flowParams = flowDetailResp?.data?.data?.default_params || {};
        } catch (e) {
          console.error('Failed to fetch flow details:', e);
        }
      } else if (item_type === 'step' && step_id) {
        try {
          const stepDetailResp = await getStep(step_id);
          const stepDetail = stepDetailResp?.data?.data;
          stepActionValue = stepDetail?.action_value || '';
          // 提取 action_value 中的模板参数
          stepParams = extractTemplateParams(stepActionValue);
        } catch (e) {
          console.error('Failed to fetch step details:', e);
        }
      }

      // testcase_items 只保存参数名，不保存参数值
      // 参数值统一在 testcase.params 中管理
      console.log('保存的 detected_params:', manualParams);
      console.log('参数名数量:', manualParams.length);

      const newItem: TestcaseItem = {
        id: editingIndex >= 0 ? items[editingIndex].id : Date.now(),
        testcase_id: testcaseId || 0,
        item_type,
        flow_id: item_type === 'flow' ? flow_id : undefined,
        step_id: item_type === 'step' ? step_id : undefined,
        order_index,
        enabled,
        continue_on_error,
        params: {}, // 不保存参数值，只保存空对象
        flow_name: item_type === 'flow' ? selectedFlow?.name : undefined,
        step_name: item_type === 'step' ? selectedStep?.name : undefined,
        step_action_type: item_type === 'step' ? selectedStep?.action_type : undefined,
        step_action_value: stepActionValue || undefined,
        flow_params: Object.keys(flowParams).length > 0 ? flowParams : undefined,
        step_params: stepParams.length > 0 ? stepParams : undefined,
        detected_params: manualParams.length > 0 ? [...manualParams] : undefined,  // 保存识别到的参数名
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      let newItems: TestcaseItem[];
      if (editingIndex >= 0) {
        newItems = [...items];
        newItems[editingIndex] = newItem;
      } else {
        newItems = [...items, newItem];
        // 重新排序
        newItems.sort((a, b) => a.order_index - b.order_index);
      }

      setItems(newItems);
      onChange(newItems);
      setAddModalOpen(false);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const itemTypeColor = (type: string) => {
    return type === 'flow' ? 'blue' : 'green';
  };

  // 提取字符串中的模板参数
  // 支持多种语法：{{param}}, {[param]}, {param}, <%param%>, ${param}
  const extractTemplateParams = (text: string): string[] => {
    if (!text) return [];

    const params = new Set<string>();

    // 匹配 {{param}}
    let regex = /\{\{([^}]+)\}\}/g;
    let match;
    while ((match = regex.exec(text)) !== null) {
      params.add(match[1]);
    }

    // 匹配 {[param]}
    regex = /\{\[([^\]]+)\]\}/g;
    while ((match = regex.exec(text)) !== null) {
      params.add(match[1]);
    }

    // 匹配 ${param}
    regex = /\$\{([^}]+)\}/g;
    while ((match = regex.exec(text)) !== null) {
      params.add(match[1]);
    }

    // 匹配 <%param%>
    regex = /<%([^%]+)%>/g;
    while ((match = regex.exec(text)) !== null) {
      params.add(match[1]);
    }

    return Array.from(params);
  };

  // 支持的参数格式说明（使用字符串变量避免 JSX 解析问题）
  const PARAM_FORMATS = '{{param}}, {[param]}, ${param}, <%param%>';
  const ELEMENT_LOCATOR_EXAMPLE = "//*[text()='{{test_name}}']";

  // 拖拽开始
  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  // 拖拽经过
  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;
    setDragOverIndex(index);
  };

  // 拖拽离开
  const handleDragLeave = () => {
    setDragOverIndex(null);
  };

  // 拖拽结束
  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === dropIndex) {
      setDraggedIndex(null);
      setDragOverIndex(null);
      return;
    }

    const newItems = [...items];
    const [draggedItem] = newItems.splice(draggedIndex, 1);
    newItems.splice(dropIndex, 0, draggedItem);

    // 更新 order_index
    newItems.forEach((item, i) => {
      item.order_index = i + 1;
    });

    setItems(newItems);
    onChange(newItems);

    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加 Item
        </Button>
        <span style={{ marginLeft: 12, color: '#8c8c8c' }}>
          支持 Flow 和 Step 混排，可拖拽排序
        </span>
      </div>

      {items.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '40px 0',
            color: '#8c8c8c',
            border: '1px dashed #d9d9d9',
            borderRadius: 4,
          }}
        >
          暂无 Items，点击上方按钮添加
        </div>
      ) : (
        <Space orientation="vertical" style={{ width: '100%' }} size="small">
          {items.map((item, index) => (
            <div
              key={item.id}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, index)}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '12px',
                border: `1px solid ${dragOverIndex === index ? '#1890ff' : '#d9d9d9'}`,
                borderRadius: 4,
                background: item.enabled ? '#fff' : '#f5f5f5',
                cursor: 'move',
                opacity: draggedIndex === index ? 0.5 : 1,
                transition: 'all 0.2s',
              }}
            >
              <DragOutlined style={{ marginRight: 8, color: '#8c8c8c', cursor: 'grab' }} />

              <Tag color={itemTypeColor(item.item_type)}>{item.item_type.toUpperCase()}</Tag>

              <span style={{ flex: 1, fontWeight: 500 }}>
                {item.item_type === 'flow' ? item.flow_name || `Flow-${item.flow_id}` : item.step_name || `Step-${item.step_id}`}
              </span>

              {item.item_type === 'step' && item.step_action_type && (
                <Tag color="default">{item.step_action_type}</Tag>
              )}

              {/* Flow 参数显示 */}
              {item.item_type === 'flow' && item.flow_params && Object.keys(item.flow_params).length > 0 && (
                <Tag color="purple" style={{ cursor: 'help' }} title={`参数: ${JSON.stringify(item.flow_params)}`}>
                  参数 ({Object.keys(item.flow_params).length})
                </Tag>
              )}

              {/* Step 参数显示 */}
              {item.item_type === 'step' && item.detected_params && item.detected_params.length > 0 && (
                <Tag
                  color="purple"
                  style={{ cursor: 'help' }}
                  title={`识别到的参数: ${item.detected_params.join(', ')}`}
                >
                  参数 ({item.detected_params.length})
                </Tag>
              )}

              {item.continue_on_error && <Tag color="orange">失败继续</Tag>}

              {!item.enabled && <Tag color="default">已禁用</Tag>}

              <Space size="small">
                <Switch
                  size="small"
                  checked={item.enabled}
                  onChange={() => handleToggleEnabled(index)}
                  checkedChildren="启用"
                  unCheckedChildren="禁用"
                />

                <Button
                  size="small"
                  disabled={index === 0}
                  onClick={() => handleMoveUp(index)}
                  title="上移"
                >
                  ↑
                </Button>
                <Button
                  size="small"
                  disabled={index === items.length - 1}
                  onClick={() => handleMoveDown(index)}
                  title="下移"
                >
                  ↓
                </Button>
                <Button size="small" onClick={() => handleEdit(index)}>
                  编辑
                </Button>
                <Popconfirm title="确认删除该 Item？" onConfirm={() => handleDelete(index)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            </div>
          ))}
        </Space>
      )}

      {/* 参数汇总区域 */}
      {items.length > 0 && (() => {
        // 收集所有识别到的参数
        const allDetectedParams = new Set<string>();
        items.forEach((item) => {
          if (item.detected_params && Array.isArray(item.detected_params)) {
            item.detected_params.forEach((paramName) => {
              allDetectedParams.add(paramName);
            });
          }
        });

        const paramArray = Array.from(allDetectedParams);

        if (paramArray.length === 0) {
          return null;
        }

        return (
          <div style={{
            marginTop: 16,
            padding: '12px',
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: 4
          }}>
            <div style={{ marginBottom: 8, fontWeight: 500, color: '#52c41a' }}>
              📋 识别到的参数（请在用例编辑界面的"参数(JSON)"字段中填写值）
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {paramArray.map((param) => (
                <Tag key={param} color="green">
                  {param}
                </Tag>
              ))}
            </div>
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              共 {paramArray.length} 个参数需要在用例级别配置
            </div>
          </div>
        );
      })()}

      <Modal
        title={editingIndex >= 0 ? '编辑 Item' : '添加 Item'}
        open={addModalOpen}
        onCancel={() => {
          setAddModalOpen(false);
          form.resetFields();
        }}
        onOk={handleModalOk}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="item_type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select
              options={[
                { label: 'Flow（执行整个流程）', value: 'flow' },
                { label: 'Step（执行单个步骤）', value: 'step' },
              ]}
              onChange={() => {
                form.setFieldsValue({ flow_id: undefined, step_id: undefined });
              }}
            />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.item_type !== curr.item_type}>
            {({ getFieldValue }) =>
              getFieldValue('item_type') === 'flow' ? (
                <Form.Item
                  name="flow_id"
                  label="选择 Flow"
                  rules={[{ required: true, message: '请选择 Flow' }]}
                >
                  <Select
                    showSearch
                    optionFilterProp="label"
                    options={flowOptions}
                    placeholder="选择要执行的 Flow"
                  />
                </Form.Item>
              ) : (
                <Form.Item
                  name="step_id"
                  label="选择 Step"
                  rules={[{ required: true, message: '请选择 Step' }]}
                >
                  <Select
                    showSearch
                    optionFilterProp="label"
                    options={stepOptions}
                    placeholder="选择要执行的 Step"
                    onChange={async (stepId) => {
                      if (stepId) {
                        try {
                          const stepResp = await getStep(stepId);
                          const stepDetail = stepResp?.data?.data;
                          setSelectedStepDetail(stepDetail);

                          // 如果 Step 关联了 Element，获取 Element 的 locators 并提取参数
                          if (stepDetail?.element_id) {
                            try {
                              const elementResp = await getElement(stepDetail.element_id);
                              const element = elementResp?.data?.data;
                              if (element?.locators && Array.isArray(element.locators)) {
                                // 从所有 locator 的 value 中提取参数
                                const allParams = new Set<string>();
                                element.locators.forEach((locator: any) => {
                                  if (locator.value) {
                                    const params = extractTemplateParams(locator.value);
                                    params.forEach(param => allParams.add(param));
                                  }
                                });

                                if (allParams.size > 0) {
                                  setManualParams(Array.from(allParams));
                                } else {
                                  setManualParams([]);
                                }
                              }
                            } catch (e) {
                              console.error('Failed to fetch element details:', e);
                              setManualParams([]);
                            }
                          } else {
                            setManualParams([]);
                          }
                        } catch (e) {
                          console.error('Failed to fetch step details:', e);
                          setSelectedStepDetail(null);
                          setManualParams([]);
                        }
                      } else {
                        setSelectedStepDetail(null);
                        setManualParams([]);
                      }
                    }}
                  />
                </Form.Item>
              )
            }
          </Form.Item>

          <Form.Item name="order_index" label="顺序" initialValue={items.length + 1}>
            <InputNumber min={1} max={1000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="enabled" label="启用" valuePropName="checked" initialValue={true}>
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>

          <Form.Item
            name="continue_on_error"
            label="失败继续执行"
            valuePropName="checked"
            initialValue={false}
            tooltip="如果启用，该 Item 执行失败后将继续执行后续 Items"
          >
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>

          {/* 自动识别 Element 参数提示 */}
          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.step_id !== curr.step_id}>
            {({ getFieldValue }) => {
              const itemType = getFieldValue('item_type');
              const stepId = getFieldValue('step_id');

              if (itemType === 'step' && stepId) {
                if (manualParams.length > 0) {
                  return (
                    <div style={{ marginBottom: 16 }}>
                      <Tag color="green" icon={<span>✓</span>}>
                        已从 Element 定位符自动识别 {manualParams.length} 个参数
                      </Tag>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                        {manualParams.map((param, idx) => {
                          const paramStr = String(param || '');
                          return (
                            <Tag key={paramStr} color="blue">
                              {paramStr}
                            </Tag>
                          );
                        })}
                      </div>
                      <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                        参数值请在主界面的"参数(JSON)"字段中统一填写
                      </div>
                    </div>
                  );
                } else {
                  return (
                    <Alert
                      title="未检测到参数"
                      description="此 Step 的 Element 定位符中未检测到模板参数（如 {{param}}）。如果需要参数，请先在 Element 的定位符中添加模板语法。"
                      type="info"
                      showIcon
                      style={{ fontSize: 12, marginBottom: 16 }}
                    />
                  );
                }
              }
              return null;
            }}
          </Form.Item>

          {/* 参数编辑区域 */}
          <Form.Item noStyle shouldUpdate={(prev, curr) => true}>
            {({ getFieldValue }) => {
              const itemType = getFieldValue('item_type');
              const flowId = getFieldValue('flow_id');
              const stepId = getFieldValue('step_id');

              // Flow 参数配置
              if (itemType === 'flow' && flowId) {
                const selectedFlow = flowsResp?.data?.data?.items?.find((f: any) => f.id === flowId);
                const defaultParams = selectedFlow?.default_params || {};

                if (Object.keys(defaultParams).length > 0) {
                  return (
                    <Collapse
                      items={[
                        {
                          key: 'params',
                          label: `参数配置 (${Object.keys(defaultParams).length} 个参数)`,
                          children: (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              {Object.entries(defaultParams).map(([key, defaultValue]) => {
                                const keyStr = String(key || '');
                                const initialValue = typeof defaultValue === 'object' ? JSON.stringify(defaultValue) : String(defaultValue || '');
                                return (
                                  <Form.Item
                                    key={keyStr}
                                    name={['params', keyStr]}
                                    label={keyStr}
                                    style={{ marginBottom: 8 }}
                                    initialValue={initialValue}
                                    tooltip={`默认值: ${JSON.stringify(defaultValue)}`}
                                    getValueProps={(value) => ({
                                      value: typeof value === 'object' ? JSON.stringify(value) : (value || '')
                                    })}
                                  >
                                    <Input placeholder={`默认值: ${JSON.stringify(defaultValue)}`} />
                                  </Form.Item>
                                );
                              })}
                            </div>
                          ),
                        },
                                              ]}
                                            />
                                          );
                                        }
                                      }

                                      // Step 参数配置
                                      if (itemType === 'step' && stepId) {
                                        // 优先使用从 API 获取的详情，否则使用列表数据
                                        const actionValueRaw = selectedStepDetail?.action_value || stepsResp?.data?.data?.items?.find((s: any) => s.id === stepId)?.action_value;
                                        const actionValue = actionValueRaw ? String(actionValueRaw) : '';

                                        const templateParams = extractTemplateParams(actionValue);

                                        if (templateParams.length > 0) {
                                          return (
                                            <div style={{ marginBottom: 16 }}>
                                              <div style={{ marginBottom: 8, color: '#8c8c8c', fontSize: 12 }}>
                                                检测到参数模板: <code>{actionValue}</code>
                                              </div>
                                              <Collapse
                                                items={[
                                                  {
                                                    key: 'params',
                                                    label: `参数配置 (${templateParams.length} 个参数)`,
                                                    children: (
                                                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                        {templateParams.map((paramName) => {
                                                          const nameStr = String(paramName || '');
                                                          return (
                                                            <Form.Item
                                                              key={nameStr}
                                                              name={['params', nameStr]}
                                                              label={nameStr}
                                                              style={{ marginBottom: 8 }}
                                                              initialValue=""
                                                              tooltip={`模板中使用的参数`}
                                                              getValueProps={(value) => ({
                                                                value: typeof value === 'object' ? JSON.stringify(value) : (value || '')
                                                              })}
                                                            >
                                                              <Input placeholder={`输入 ${nameStr} 的值`} />
                                                            </Form.Item>
                                                          );
                                                        })}
                                                      </div>
                                                    ),
                                                  },
                                                ]}
                                              />
                                            </div>
                                          );
                                        } else {
                                          // 显示提示信息，表明已检测但没有参数
                                          if (actionValue && selectedStepDetail) {
                                            return (
                                              <div style={{ marginBottom: 16, padding: 8, background: '#f5f5f5', borderRadius: 4, fontSize: 12, color: '#666' }}>
                                                该步骤的 action_value: <code>{actionValue}</code><br/>
                                                未检测到模板参数（支持的格式: {PARAM_FORMATS}）
                                              </div>
                                            );
                                          }
                                        }
                                      }

                                      return null;
                                    }}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TestcaseItemsEditor;
