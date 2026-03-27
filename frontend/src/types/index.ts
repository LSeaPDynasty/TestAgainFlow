// ============ 基础类型 ============

export interface Tag {
  id: number;
  name: string;
  color?: string;
}

export interface Locator {
  id?: number;
  type: string;
  value: string;
  priority: number;
}

// ============ Screen 相关 ============

export interface Screen {
  id: number;
  name: string;
  description?: string;
  app_id?: number;
  element_count: number;
  created_at: string;
  updated_at: string;
}

export interface ScreenCreate {
  name: string;
  description?: string;
  app_id?: number;
}

// ============ Element 相关 ============

export interface Element {
  id: number;
  name: string;
  description?: string;
  screen_id: number;
  screen_name?: string;
  locators: Locator[];
  created_at: string;
  updated_at: string;
}

export interface ElementCreate {
  name: string;
  description?: string;
  screen_id: number;
  locators: Locator[];
}

// ============ Step 相关 ============

export interface AssertConfig {
  type: string;
  expected?: string;
  on_fail: string;
}

export interface Step {
  id: number;
  name: string;
  screen_id: number;
  screen_name?: string;
  element_id?: number;
  element_name?: string;
  action_type: string;
  action_value?: string;
  assert_config?: AssertConfig;
  wait_after_ms: number;
  description?: string;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

export interface StepCreate {
  name: string;
  screen_id: number;
  element_id?: number;
  action_type: string;
  action_value?: string;
  assert_config?: AssertConfig;
  wait_after_ms?: number;
  description?: string;
  tag_ids?: number[];
}

// ============ Flow 相关 ============

export interface Flow {
  id: number;
  name: string;
  description?: string;
  flow_type: 'standard' | 'dsl' | 'python';
  requires?: string[];
  default_params?: Record<string, any>;
  dsl_content?: string;
  py_file?: string;
  step_count: number;
  expanded_step_count: number;
  tags: Tag[];
  referenced_by_testcase_count: number;
  created_at: string;
  updated_at: string;
}

export interface FlowDetail extends Flow {
  steps: FlowStep[];
}

export interface FlowStep {
  order: number;
  step_id: number;
  step_name: string;
  action_type: string;
  screen_name?: string;
  element_name?: string;
  override_value?: string;
}

export interface FlowCreate {
  name: string;
  description?: string;
  flow_type: 'standard' | 'dsl' | 'python';
  dsl_content?: string;
  requires?: string[];
  default_params?: Record<string, any>;
  steps?: Array<{ step_id: number; order: number; override_value?: string }>;
  tag_ids?: number[];
}

export interface DslValidateResponse {
  valid: boolean;
  errors: string[];
  expanded_steps: any[];
  expanded_count: number;
}

// ============ Testcase 相关 ============

export interface Testcase {
  id: number;
  name: string;
  description?: string;
  priority: string;
  timeout: number;
  enabled: boolean;
  params?: Record<string, any>;
  tags: Tag[];
  setup_flow_count: number;
  main_flow_count: number;
  teardown_flow_count: number;
  step_count: number;
  estimated_duration: number;
  suite_count: number;
  created_at: string;
  updated_at: string;
}

export interface TestcaseDetail extends Testcase {
  setup_flows: TestcaseFlow[];
  main_flows: TestcaseFlow[];
  teardown_flows: TestcaseFlow[];
  inline_steps: Step[];
}

export interface TestcaseFlow {
  id: number;
  flow_id: number;
  flow_name?: string;
  flow_role: 'setup' | 'main' | 'teardown';
  order: number;
  enabled: boolean;
  params?: Record<string, any>;
}

export interface TestcaseCreate {
  name: string;
  description?: string;
  priority: string;
  timeout?: number;
  enabled?: boolean;
  params?: Record<string, any>;
  setup_flows?: Array<{ flow_id: number; order: number; enabled?: boolean; params?: Record<string, any> }>;
  main_flows?: Array<{ flow_id: number; order: number; enabled?: boolean; params?: Record<string, any> }>;
  teardown_flows?: Array<{ flow_id: number; order: number; enabled?: boolean; params?: Record<string, any> }>;
  inline_steps?: Array<{ step_id: number; order: number }>;
  tag_ids?: number[];
}

export interface DependencyChain {
  setup_flows: FlowDetail[];
  main_flows: FlowDetail[];
  teardown_flows: FlowDetail[];
  all_steps: Step[];
  required_profiles: string[];
}

// ============ Suite 相关 ============

export interface Suite {
  id: number;
  name: string;
  description?: string;
  enabled: boolean;
  tags: Tag[];
  testcase_count: number;
  total_step_count: number;
  estimated_duration: number;
  created_at: string;
  updated_at: string;
}

export interface SuiteDetail extends Suite {
  testcases: Array<{
    id: number;
    name: string;
    priority: string;
    enabled: boolean;
    order: number;
  }>;
}

export interface SuiteCreate {
  name: string;
  description?: string;
  enabled?: boolean;
  testcase_ids?: number[];
  tag_ids?: number[];
}

// ============ Profile 相关 ============

export interface Profile {
  id: number;
  name: string;
  description?: string;
  data: Record<string, Record<string, string>>;
  tags: Tag[];
  is_global: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProfileCreate {
  name: string;
  description?: string;
  data: Record<string, Record<string, string>>;
  tag_ids?: number[];
}

// ============ Device 相关 ============

export interface Device {
  id: number;
  serial: string;
  name: string;
  status: string;
  device_type: string;
  os_version: string;
  app_version?: string;
  screen_size: string;
  properties?: Record<string, any>;
  last_online?: string;
  created_at: string;
  updated_at: string;
}

export interface DeviceCreate {
  serial: string;
  name: string;
  device_type: string;
  os_version: string;
  screen_size: string;
  properties?: Record<string, any>;
}

// ============ Run 相关 ============

export interface RunHistory {
  id: number;
  task_id: string;
  type: string;
  target_ids: number[];
  target_names?: string[];
  device_serial: string;
  device_name?: string;
  result: 'running' | 'success' | 'failed' | 'stopped' | 'timeout';
  total_count: number;
  success_count: number;
  failed_count: number;
  skipped_count: number;
  started_at: string;
  finished_at?: string;
  error_message?: string;
}

export interface RunCreate {
  type: 'testcase' | 'suite';
  target_ids: number[];
  device_serial: string;
  config?: {
    stop_on_failure?: boolean;
    screenshot_on_failure?: boolean;
    max_retries?: number;
  };
}

export interface RunStatus {
  task_id: string;
  status: string;
  progress: number;
  current_step?: string;
  result?: string;
  total_count: number;
  success_count: number;
  failed_count: number;
  started_at: string;
}

// ============ DataStore 相关 ============

export interface DataStore {
  [env: string]: {
    [key: string]: string;
  };
}
