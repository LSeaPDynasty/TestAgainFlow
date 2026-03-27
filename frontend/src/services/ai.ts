/**
 * AI Service - AI-powered test automation features
 */

import api from './api';

export interface DOMElement {
  text?: string;
  'resource-id'?: string;
  class?: string;
  'content-desc'?: string;
  xpath?: string;
  bounds?: string;
}

export interface ElementSuggestRequest {
  dom_element: DOMElement;
  screen_id?: number;
  project_id?: number;
  threshold?: number;
}

export interface ElementMatch {
  element_id: number;
  element_name: string;
  similarity_score: number;
  match_type: 'strict' | 'fuzzy' | 'semantic';
  reason: string;
  locators: Array<{
    type: string;
    value: string;
    priority: number;
  }>;
}

export interface ElementSuggestResponse {
  matches: ElementMatch[];
  can_create_new: boolean;
  best_match?: ElementMatch;
  search_summary?: {
    strict_matches: number;
    fuzzy_matches: number;
    ai_analyzed: number;
  };
  ai_recommendation?: {
    recommendation: 'reuse' | 'create_new';
    suggested_name?: string;
    suggested_locators?: Array<{
      type: string;
      value: string;
      priority: number;
    }>;
  };
}

export interface TestcaseGenerateRequest {
  json_data: Record<string, any>;
  project_id?: number;
}

export interface ResourceRecommendation {
  type: 'reuse_flow' | 'reuse_step' | 'create_flow' | 'create_step' | 'create_element';
  flow_id?: number;
  step_id?: number;
  element_id?: number;
  name?: string;
  confidence: number;
  reason: string;
}

export interface TestcasePlan {
  name: string;
  description: string;
  structure: {
    approach: 'single_flow' | 'mixed' | 'inline_steps';
    main_flow_id?: number;
    flow_steps?: Array<{
      step_id?: number;
      step_name?: string;
      step_type?: string;
      element_id?: number;
      element_name?: string;
      value?: string;
      description: string;
    }>;
  };
}

export interface TestcaseGenerateResponse {
  success: boolean;
  plan?: TestcasePlan;
  recommendations: ResourceRecommendation[];
  resources_found: {
    elements: number;
    steps: number;
    flows: number;
  };
  missing_resources: {
    elements: string[];
    steps: string[];
  };
  analysis?: {
    goal?: string;
    key_actions?: string[];
  };
  ai_stats?: {
    input_tokens?: number;
    output_tokens?: number;
    cost_usd?: number;
    latency_ms?: number;
  };
  error?: string;
}

export interface AIConfig {
  id: number;
  provider: 'openai' | 'zhipu' | 'custom';
  name: string;
  is_active: boolean;
  priority: number;
  config: {
    api_key?: string;
    base_url?: string;
    model?: string;
    timeout?: number;
    max_retries?: number;
    extra_params?: Record<string, any>;
  };
  created_at: string;
  updated_at: string;
}

export interface AIConfigCreate {
  provider: string;
  name: string;
  config_data: Record<string, any>;
  priority?: number;
  is_active?: boolean;
}

export interface DailyStats {
  date: string;
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  daily_limit_usd: number;
  remaining_budget_usd: number;
}

/**
 * AI Service API
 */
export const aiService = {
  /**
   * Get element suggestions from DOM element
   */
  suggestElements: async (data: ElementSuggestRequest): Promise<ElementSuggestResponse> => {
    const response = await api.post('/ai/elements/suggest', data);
    return response.data.data;
  },

  /**
   * Generate test case plan from JSON
   */
  generateTestcase: async (data: TestcaseGenerateRequest): Promise<TestcaseGenerateResponse> => {
    const response = await api.post('/ai/testcases/generate', data);
    return response.data.data;
  },

  /**
   * Generate a single step from description
   */
  generateStep: async (
    stepDescription: string,
    projectId?: number
  ): Promise<{ success: boolean; step?: any; error?: string }> => {
    const params = new URLSearchParams();
    params.append('step_description', stepDescription);
    if (projectId !== undefined) {
      params.append('project_id', projectId.toString());
    }

    const response = await api.post(`/ai/steps/generate?${params.toString()}`);
    return response.data.data;
  },

  /**
   * List AI configurations
   */
  listConfigs: async (activeOnly = false): Promise<AIConfig[]> => {
    const response = await api.get('/ai/config', { params: { active_only: activeOnly } });
    return response.data.data;
  },

  /**
   * Get AI configuration by ID
   */
  getConfig: async (configId: number): Promise<AIConfig> => {
    const response = await api.get(`/ai/config/${configId}`);
    return response.data.data;
  },

  /**
   * Get active AI configuration
   */
  getActiveConfig: async (profileId?: number): Promise<AIConfig | null> => {
    const params = profileId ? { profile_id: profileId } : {};
    const response = await api.get('/ai/config/active', { params });
    return response.data.data;
  },

  /**
   * Create AI configuration
   */
  createConfig: async (data: AIConfigCreate): Promise<AIConfig> => {
    const response = await api.post('/ai/config', data);
    return response.data.data;
  },

  /**
   * Update AI configuration
   */
  updateConfig: async (
    configId: number,
    data: Partial<AIConfigCreate>
  ): Promise<AIConfig> => {
    const response = await api.put(`/ai/config/${configId}`, data);
    return response.data.data;
  },

  /**
   * Delete AI configuration
   */
  deleteConfig: async (configId: number): Promise<void> => {
    await api.delete(`/ai/config/${configId}`);
  },

  /**
   * Test AI configuration
   */
  testConfig: async (
    provider: string,
    configData: Record<string, any>
  ): Promise<{ success: boolean; latency_ms?: number }> => {
    const response = await api.post('/ai/config/test', { provider, config_data: configData });
    return response.data.data;
  },

  /**
   * Get daily usage statistics
   */
  getDailyStats: async (provider?: string): Promise<DailyStats> => {
    const params = provider ? { provider } : {};
    const response = await api.get('/ai/stats/daily', { params });
    return response.data.data;
  },

  /**
   * Get recent request logs
   */
  getRecentLogs: async (
    limit = 100,
    provider?: string,
    status?: string
  ): Promise<
    Array<{
      id: number;
      provider: string;
      model: string;
      request_type: string;
      input_tokens?: number;
      output_tokens?: number;
      cost_usd?: number;
      latency_ms?: number;
      status: string;
      created_at: string;
    }>
  > => {
    const params: any = { limit };
    if (provider) params.provider = provider;
    if (status) params.status = status;

    const response = await api.get('/ai/logs/recent', { params });
    return response.data.data;
  },
};

export default aiService;
