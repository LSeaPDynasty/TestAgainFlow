import React, { useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Divider,
  Drawer,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Upload,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { UploadProps } from 'antd';
import {
  CopyOutlined,
  DeleteOutlined,
  EditOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../../contexts/ProjectContext';
import TestcaseItemsEditor from '../../components/TestcaseItemsEditor';
import {
  createTestcase,
  deleteTestcase,
  duplicateTestcase,
  getTestcase,
  getTestcases,
  importTestcasesBatch,
  updateTestcase,
  updateTestcaseItems,
  type Testcase,
  type TestcaseItem,
} from '../../services/testcase';
import { getFlows } from '../../services/flow';
import { getDevices } from '../../services/device';
import { createRun } from '../../services/run';

const { Search, TextArea } = Input;
const { Dragger } = Upload;

const PRIORITIES = [
  { value: 'P0', color: 'red' },
  { value: 'P1', color: 'orange' },
  { value: 'P2', color: 'gold' },
  { value: 'P3', color: 'default' },
] as const;

type FormData = {
  name: string;
  description?: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  timeout: number;
  paramsText?: string;
  setup_flow_ids?: number[];
  main_flow_ids?: number[];
  teardown_flow_ids?: number[];
  use_items?: boolean;
  testcase_items?: TestcaseItem[];
};

const toFlowPayload = (ids: number[] | undefined) =>
  (ids || []).map((flowId, idx) => ({
    flow_id: Number(flowId),
    order: idx + 1,
    enabled: true,
  }));

const mergeDetectedParams = (items: TestcaseItem[] | undefined, params: Record<string, any>) => {
  const detectedNames = new Set<string>();
  (items || []).forEach((item: any) => {
    if (Array.isArray(item?.detected_params)) {
      item.detected_params.forEach((name: string) => detectedNames.add(name));
    }
  });

  if (detectedNames.size === 0) {
    return params;
  }

  const merged: Record<string, any> = {};
  detectedNames.forEach((name) => {
    merged[name] = params[name] !== undefined ? params[name] : '';
  });

  Object.keys(params).forEach((key) => {
    if (!detectedNames.has(key)) {
      merged[key] = params[key];
    }
  });

  return merged;
};

const normalizeItemParams = (items: any[]): TestcaseItem[] =>
  (items || []).map((item: any) => {
    const raw = item?.params;
    if (!raw || typeof raw !== 'object') {
      return item;
    }
    const params: Record<string, string> = {};
    Object.entries(raw).forEach(([k, v]) => {
      params[k] = typeof v === 'object' && v !== null ? JSON.stringify(v) : String(v ?? '');
    });
    return { ...item, params };
  });

const toApiItems = (items: TestcaseItem[]) =>
  items.map((item, idx) => ({
    item_type: item.item_type,
    flow_id: item.flow_id,
    step_id: item.step_id,
    order_index: idx + 1,
    enabled: item.enabled ?? true,
    continue_on_error: item.continue_on_error ?? false,
    params: item.params || {},
  }));

const TestcasesPage: React.FC = () => {
  const { selectedProjectId } = useProject();
  const queryClient = useQueryClient();

  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const [editOpen, setEditOpen] = useState(false);
  const [editing, setEditing] = useState<Testcase | null>(null);
  const [form] = Form.useForm<FormData>();

  const [executeOpen, setExecuteOpen] = useState(false);
  const [batchExecuteOpen, setBatchExecuteOpen] = useState(false);
  const [selectedForExecute, setSelectedForExecute] = useState<Testcase | null>(null);
  const [deviceSerial, setDeviceSerial] = useState('');

  const [importOpen, setImportOpen] = useState(false);
  const [importJson, setImportJson] = useState('');
  const [importFileName, setImportFileName] = useState('');
  const [importResult, setImportResult] = useState<any | null>(null);

  const { data: testcaseResp, isLoading } = useQuery({
    queryKey: ['testcases', page, pageSize, searchText, selectedProjectId],
    queryFn: () =>
      getTestcases({
        page,
        page_size: pageSize,
        search: searchText || undefined,
        project_id: selectedProjectId || undefined,
      }),
  });

  const { data: flowsResp } = useQuery({
    queryKey: ['flows-for-testcase-form', selectedProjectId],
    queryFn: () => getFlows({ page: 1, page_size: 1000, project_id: selectedProjectId || undefined }),
  });

  const { data: devicesResp } = useQuery({
    queryKey: ['devices-for-testcase-run'],
    queryFn: () => getDevices({ page: 1, page_size: 200 }),
  });

  const testcases: Testcase[] = testcaseResp?.data?.data?.items || [];
  const total = testcaseResp?.data?.data?.total || 0;
  const flowOptions = (flowsResp?.data?.data?.items || []).map((f: any) => ({ label: f.name, value: f.id }));
  const deviceOptions = (devicesResp?.data?.data?.items || []).map((d: any) => ({
    label: `${d.name || d.serial} (${d.status})`,
    value: d.serial,
    disabled: d.status !== 'online',
  }));

  const createMutation = useMutation({
    mutationFn: createTestcase,
    onSuccess: () => {
      message.success('创建成功');
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ['testcases'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '创建失败'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: any }) => updateTestcase(id, payload),
    onSuccess: () => {
      message.success('更新成功');
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ['testcases'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '更新失败'),
  });

  const duplicateMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) => duplicateTestcase(id, { new_name: name }),
    onSuccess: () => {
      message.success('复制成功');
      queryClient.invalidateQueries({ queryKey: ['testcases'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '复制失败'),
  });

  const singleExecuteMutation = useMutation({
    mutationFn: ({ testcaseId, serial }: { testcaseId: number; serial: string }) =>
      createRun({ type: 'testcase', target_ids: [testcaseId], device_serial: serial }),
    onSuccess: () => {
      message.success('执行任务已创建');
      setExecuteOpen(false);
      setDeviceSerial('');
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '执行失败'),
  });

  const importMutation = useMutation({
    mutationFn: importTestcasesBatch,
    onSuccess: (resp: any) => {
      const result = resp?.data?.data || null;
      setImportResult(result);
      const successCount = result?.count || 0;
      const failedCount = result?.failed?.length || 0;
      if (failedCount > 0) {
        message.warning(`导入完成：成功 ${successCount}，失败 ${failedCount}`);
      } else {
        message.success(`导入成功：${successCount} 个用例`);
      }
      queryClient.invalidateQueries({ queryKey: ['testcases'] });
    },
    onError: (e: any) => message.error(e?.response?.data?.message || '导入失败'),
  });

  const tableColumns: ColumnsType<Testcase> = useMemo(
    () => [
      { title: 'ID', dataIndex: 'id', width: 80 },
      { title: '名称', dataIndex: 'name', width: 260 },
      {
        title: '优先级',
        dataIndex: 'priority',
        width: 100,
        render: (v: string) => <Tag color={PRIORITIES.find((p) => p.value === v)?.color || 'default'}>{v}</Tag>,
      },
      {
        title: '流程数',
        width: 280,
        render: (_: any, r: Testcase) => (
          <Space>
            {r.testcase_item_count > 0 ? (
              <Tag color="purple">items {r.testcase_item_count}</Tag>
            ) : (
              <>
                <Tag color="green">setup {r.setup_flow_count}</Tag>
                <Tag color="blue">main {r.main_flow_count}</Tag>
                <Tag color="orange">teardown {r.teardown_flow_count}</Tag>
              </>
            )}
          </Space>
        ),
      },
      { title: '超时(秒)', dataIndex: 'timeout', width: 110 },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        width: 180,
        render: (v: string) => new Date(v).toLocaleString(),
      },
      {
        title: '操作',
        width: 220,
        fixed: 'right',
        render: (_: any, row: Testcase) => (
          <Space>
            <Button size="small" icon={<PlayCircleOutlined />} onClick={() => openSingleExecute(row)} />
            <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(row)} />
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => duplicateMutation.mutate({ id: row.id, name: `${row.name}-副本` })}
            />
            <Popconfirm title="确认删除该用例？" onConfirm={() => handleDeleteOne(row.id)}>
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [duplicateMutation],
  );

  const resetFormForCreate = () => {
    setEditing(null);
    form.setFieldsValue({
      name: '',
      description: '',
      priority: 'P1',
      timeout: 120,
      paramsText: '{}',
      setup_flow_ids: [],
      main_flow_ids: [],
      teardown_flow_ids: [],
      use_items: true,
      testcase_items: [],
    });
    setEditOpen(true);
  };

  async function openEdit(row: Testcase) {
    setEditing(row);
    try {
      const detailResp = await getTestcase(row.id);
      const detail = detailResp?.data?.data;
      const testcaseItems = normalizeItemParams(detail?.testcase_items || []);
      form.setFieldsValue({
        name: detail?.name || row.name,
        description: detail?.description || row.description || '',
        priority: detail?.priority || row.priority,
        timeout: detail?.timeout || row.timeout || 120,
        paramsText: detail?.params ? JSON.stringify(detail.params, null, 2) : '{}',
        setup_flow_ids: (detail?.setup_flows || []).map((x: any) => x.flow_id),
        main_flow_ids: (detail?.main_flows || []).map((x: any) => x.flow_id),
        teardown_flow_ids: (detail?.teardown_flows || []).map((x: any) => x.flow_id),
        use_items: testcaseItems.length > 0,
        testcase_items: testcaseItems,
      });
    } catch {
      form.setFieldsValue({
        name: row.name,
        description: row.description || '',
        priority: (row.priority as FormData['priority']) || 'P1',
        timeout: row.timeout || 120,
        paramsText: row.params ? JSON.stringify(row.params, null, 2) : '{}',
        setup_flow_ids: [],
        main_flow_ids: [],
        teardown_flow_ids: [],
        use_items: true,
        testcase_items: [],
      });
    }
    setEditOpen(true);
  }

  const parseParamsText = (paramsText?: string) => {
    if (!paramsText?.trim()) {
      return undefined;
    }
    try {
      return JSON.parse(paramsText);
    } catch {
      message.error('参数 JSON 格式错误');
      return null;
    }
  };

  const submitEdit = async () => {
    const values = await form.validateFields();
    const parsedParams = parseParamsText(values.paramsText);
    if (parsedParams === null) {
      return;
    }

    const basePayload: any = {
      name: values.name,
      description: values.description,
      priority: values.priority,
      timeout: values.timeout,
      params: parsedParams,
      setup_flows: toFlowPayload(values.setup_flow_ids),
      teardown_flows: toFlowPayload(values.teardown_flow_ids),
    };

    if (values.use_items) {
      const items = values.testcase_items || [];
      if (items.length === 0) {
        message.warning('请至少添加一个 Main Item');
        return;
      }
      basePayload.params = mergeDetectedParams(items, parsedParams || {});
      const apiItems = toApiItems(items);

      if (editing) {
        await updateTestcase(editing.id, basePayload);
        await updateTestcaseItems(editing.id, apiItems);
        message.success('更新成功');
      } else {
        const createResp = await createTestcase(basePayload);
        const newId = createResp?.data?.data?.id;
        if (newId) {
          await updateTestcaseItems(newId, apiItems);
        }
        message.success('创建成功');
      }
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ['testcases'] });
      return;
    }

    basePayload.main_flows = toFlowPayload(values.main_flow_ids);
    if (!basePayload.main_flows?.length) {
      message.warning('主流程至少选择一个');
      return;
    }

    if (editing) {
      updateMutation.mutate({ id: editing.id, payload: basePayload });
    } else {
      createMutation.mutate(basePayload);
    }
  };

  async function handleDeleteOne(id: number) {
    try {
      await deleteTestcase(id);
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['testcases'] });
    } catch (e: any) {
      message.error(e?.response?.data?.message || '删除失败');
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择用例');
      return;
    }
    try {
      await Promise.all(selectedRowKeys.map((id) => deleteTestcase(Number(id))));
      message.success(`已删除 ${selectedRowKeys.length} 个用例`);
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['testcases'] });
    } catch (e: any) {
      message.error(e?.response?.data?.message || '批量删除失败');
    }
  };

  function openSingleExecute(row: Testcase) {
    setSelectedForExecute(row);
    setDeviceSerial('');
    setExecuteOpen(true);
  }

  const confirmSingleExecute = () => {
    if (!selectedForExecute) {
      return;
    }
    if (!deviceSerial) {
      message.warning('请选择设备');
      return;
    }
    singleExecuteMutation.mutate({ testcaseId: selectedForExecute.id, serial: deviceSerial });
  };

  const confirmBatchExecute = async () => {
    if (!deviceSerial) {
      message.warning('请选择设备');
      return;
    }
    if (!selectedRowKeys.length) {
      message.warning('请先选择要执行的用例');
      return;
    }
    try {
      await createRun({
        type: 'testcase',
        target_ids: selectedRowKeys.map((id) => Number(id)),
        device_serial: deviceSerial,
      });
      message.success(`已创建 ${selectedRowKeys.length} 个用例的执行任务`);
      setBatchExecuteOpen(false);
      setDeviceSerial('');
    } catch (e: any) {
      message.error(e?.response?.data?.message || '批量执行失败');
    }
  };

  const submitImport = () => {
    if (!importJson.trim()) {
      message.warning('请先上传或粘贴 JSON');
      return;
    }

    try {
      const parsed = JSON.parse(importJson);
      const payload: any =
        parsed && typeof parsed === 'object' && !Array.isArray(parsed)
          ? parsed
          : { testcases: parsed, project_id: selectedProjectId || undefined };

      if (!payload.project_id && selectedProjectId) {
        payload.project_id = selectedProjectId;
      }

      setImportResult(null);
      importMutation.mutate(payload);
    } catch (e: any) {
      message.error(`JSON 格式错误: ${e?.message || 'invalid json'}`);
    }
  };

  const uploadProps: UploadProps = {
    accept: '.json,application/json',
    showUploadList: false,
    beforeUpload: (file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImportJson(String(e.target?.result || ''));
        setImportFileName(file.name);
        setImportResult(null);
      };
      reader.readAsText(file, 'utf-8');
      return false;
    },
  };

  return (
    <div>
      <Card
        title={`用例管理（共 ${total} 条）`}
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ['testcases'] })}>
              刷新
            </Button>
            <Button icon={<UploadOutlined />} onClick={() => setImportOpen(true)}>
              JSON 递归导入
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={resetFormForCreate}>
              新建用例
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Search
            allowClear
            placeholder="搜索用例名称"
            style={{ width: 260 }}
            onSearch={setSearchText}
            onChange={(e) => {
              if (!e.target.value) {
                setSearchText('');
              }
            }}
          />
          {selectedRowKeys.length > 0 ? (
            <>
              <Button icon={<ThunderboltOutlined />} onClick={() => setBatchExecuteOpen(true)}>
                批量执行 ({selectedRowKeys.length})
              </Button>
              <Popconfirm title={`确认删除选中的 ${selectedRowKeys.length} 个用例？`} onConfirm={handleBatchDelete}>
                <Button danger icon={<DeleteOutlined />}>
                  批量删除
                </Button>
              </Popconfirm>
            </>
          ) : null}
        </Space>

        <Table<Testcase>
          rowKey="id"
          loading={isLoading}
          dataSource={testcases}
          columns={tableColumns}
          rowSelection={{ selectedRowKeys, onChange: setSelectedRowKeys }}
          scroll={{ x: 1250 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            onChange: (nextPage, nextPageSize) => {
              setPage(nextPage);
              setPageSize(nextPageSize || 20);
            },
          }}
        />
      </Card>

      <Drawer
        title={editing ? '编辑用例' : '新建用例'}
        open={editOpen}
        onClose={() => setEditOpen(false)}
        width="70vw"
        destroyOnClose
        extra={
          <Space>
            <Button onClick={() => setEditOpen(false)}>取消</Button>
            <Button type="primary" loading={createMutation.isPending || updateMutation.isPending} onClick={submitEdit}>
              保存
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onValuesChange={(changedValues) => {
            if (!('testcase_items' in changedValues)) {
              return;
            }
            const items = (changedValues.testcase_items || []) as TestcaseItem[];
            const existingText = form.getFieldValue('paramsText') || '{}';
            let parsed: Record<string, any> = {};
            try {
              parsed = JSON.parse(existingText);
            } catch {
              parsed = {};
            }
            const merged = mergeDetectedParams(items, parsed);
            form.setFieldValue('paramsText', JSON.stringify(merged, null, 2));
          }}
        >
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 12 }}
            message="推荐先配置 Main，再补 Setup/Teardown；参数会根据 Main Items 自动收集。"
          />
          <Divider orientation="left">基础信息</Divider>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input />
          </Form.Item>

          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="priority" label="优先级" style={{ flex: 1 }}>
              <Select options={PRIORITIES.map((p) => ({ label: p.value, value: p.value }))} />
            </Form.Item>
            <Form.Item name="timeout" label="超时(秒)" style={{ flex: 1 }}>
              <InputNumber min={1} max={3600} style={{ width: '100%' }} />
            </Form.Item>
          </Space>

          <Form.Item name="setup_flow_ids" label="Setup Flows">
            <Select mode="multiple" showSearch optionFilterProp="label" options={flowOptions} placeholder="选择前置流程" />
          </Form.Item>

          <Divider orientation="left">Main 配置</Divider>
          <Form.Item label="Main 配置">
            <Form.Item noStyle name="use_items" valuePropName="checked">
              <Switch checkedChildren="Items" unCheckedChildren="Main Flows" />
            </Form.Item>
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.use_items !== curr.use_items}>
            {({ getFieldValue }) =>
              getFieldValue('use_items') ? (
                <Form.Item
                  name="testcase_items"
                  label="Main Items (Flow/Step 混排)"
                  rules={[{ required: true, type: 'array', min: 1, message: '请至少添加一个 Item' }]}
                >
                  <TestcaseItemsEditor
                    testcaseId={editing?.id}
                    items={form.getFieldValue('testcase_items') || []}
                    onChange={(items) => form.setFieldsValue({ testcase_items: items })}
                  />
                </Form.Item>
              ) : (
                <Form.Item
                  name="main_flow_ids"
                  label="Main Flows"
                  rules={[{ required: true, type: 'array', min: 1, message: '至少选择一个主流程' }]}
                >
                  <Select mode="multiple" showSearch optionFilterProp="label" options={flowOptions} placeholder="选择主流程" />
                </Form.Item>
              )
            }
          </Form.Item>

          <Form.Item name="teardown_flow_ids" label="Teardown Flows">
            <Select mode="multiple" showSearch optionFilterProp="label" options={flowOptions} placeholder="选择后置流程" />
          </Form.Item>

          <Divider orientation="left">运行参数</Divider>
          <Form.Item name="paramsText" label="参数(JSON)">
            <TextArea rows={7} />
          </Form.Item>
        </Form>
      </Drawer>

      <Modal
        title={`执行用例：${selectedForExecute?.name || ''}`}
        open={executeOpen}
        onCancel={() => {
          setExecuteOpen(false);
          setDeviceSerial('');
        }}
        onOk={confirmSingleExecute}
        confirmLoading={singleExecuteMutation.isPending}
      >
        <Select
          style={{ width: '100%' }}
          placeholder="选择设备"
          value={deviceSerial || undefined}
          onChange={setDeviceSerial}
          showSearch
          optionFilterProp="label"
          options={deviceOptions}
        />
      </Modal>

      <Modal
        title={`批量执行用例 (${selectedRowKeys.length})`}
        open={batchExecuteOpen}
        onCancel={() => {
          setBatchExecuteOpen(false);
          setDeviceSerial('');
        }}
        onOk={confirmBatchExecute}
      >
        <Select
          style={{ width: '100%' }}
          placeholder="选择设备"
          value={deviceSerial || undefined}
          onChange={setDeviceSerial}
          showSearch
          optionFilterProp="label"
          options={deviceOptions}
        />
      </Modal>

      <Modal
        title="JSON 递归导入"
        open={importOpen}
        width={900}
        onCancel={() => {
          setImportOpen(false);
          setImportJson('');
          setImportFileName('');
          setImportResult(null);
        }}
        onOk={submitImport}
        okText="开始导入"
        confirmLoading={importMutation.isPending}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            type="info"
            showIcon
            message="支持单用例 JSON 或批量 JSON(testcases 数组)"
            description="导入时会递归创建 screen / element / step / flow / testcase，已存在资源自动复用。"
          />

          <Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <UploadOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽 JSON 文件到这里</p>
          </Dragger>

          {importFileName ? (
            <div style={{ color: '#8c8c8c', fontSize: 12 }}>当前文件：{importFileName}</div>
          ) : null}

          <TextArea
            rows={12}
            value={importJson}
            onChange={(e) => {
              setImportJson(e.target.value);
              setImportResult(null);
            }}
            placeholder='{"name":"登录成功用例","main_flows":[...]}'
            style={{ fontFamily: 'Monaco, Menlo, monospace', fontSize: 12 }}
          />

          {importResult ? (
            <Alert
              type={(importResult.failed?.length || 0) > 0 ? 'warning' : 'success'}
              showIcon
              message={`导入结果：成功 ${importResult.count || 0}，失败 ${importResult.failed?.length || 0}`}
              description={
                <div>
                  <div>
                    创建:
                    {` ${Object.entries(importResult.details?.created || {})
                      .map(([k, v]: any) => `${k}(${Array.isArray(v) ? v.length : 0})`)
                      .join('，')}`}
                  </div>
                  <div>
                    复用:
                    {` ${Object.entries(importResult.details?.reused || {})
                      .map(([k, v]: any) => `${k}(${Array.isArray(v) ? v.length : 0})`)
                      .join('，')}`}
                  </div>
                </div>
              }
            />
          ) : null}
        </Space>
      </Modal>
    </div>
  );
};

export default TestcasesPage;
