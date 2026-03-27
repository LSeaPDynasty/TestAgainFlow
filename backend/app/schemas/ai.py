"""
AI-related request and response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# Element Suggestion Request/Response
class DOMElement(BaseModel):
    """DOM element from viewer"""
    text: Optional[str] = None
    resource_id: Optional[str] = Field(None, alias="resource-id")
    class_name: Optional[str] = Field(None, alias="class")
    content_desc: Optional[str] = Field(None, alias="content-desc")
    xpath: Optional[str] = None
    bounds: Optional[str] = None

    class Config:
        populate_by_name = True


class ElementSuggestRequest(BaseModel):
    """Request for element suggestion"""
    dom_element: DOMElement
    screen_id: Optional[int] = None
    project_id: Optional[int] = None
    threshold: float = 0.7


class ElementMatch(BaseModel):
    """Element match result"""
    element_id: int
    element_name: str
    similarity_score: float
    match_type: str  # strict, fuzzy, semantic
    reason: str
    locators: List[Dict[str, Any]]


class ElementSuggestResponse(BaseModel):
    """Response for element suggestion"""
    matches: List[ElementMatch]
    can_create_new: bool
    best_match: Optional[ElementMatch] = None
    search_summary: Optional[Dict[str, int]] = None
    ai_recommendation: Optional[Dict[str, Any]] = None


# Test Case Generation Request/Response
class TestcaseGenerateRequest(BaseModel):
    """Request for test case generation"""
    json_data: Dict[str, Any]
    project_id: Optional[int] = None


class ResourceRecommendation(BaseModel):
    """Resource reuse/create recommendation"""
    type: str  # reuse_flow, reuse_step, create_flow, create_step, create_element
    flow_id: Optional[int] = None
    step_id: Optional[int] = None
    element_id: Optional[int] = None
    name: Optional[str] = None
    confidence: float
    reason: str


class TestcasePlan(BaseModel):
    """Generated test case plan"""
    name: str
    description: str
    structure: Dict[str, Any]


class TestcaseGenerateResponse(BaseModel):
    """Response for test case generation"""
    success: bool
    plan: Optional[TestcasePlan] = None
    recommendations: List[ResourceRecommendation]
    resources_found: Dict[str, int]
    missing_resources: Dict[str, List[str]]
    analysis: Optional[Dict[str, Any]] = None
    ai_stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# AI Config Request/Response
class AIConfigCreate(BaseModel):
    """Request to create AI config"""
    provider: str  # openai, zhipu, custom
    name: str
    config_data: Dict[str, Any]
    priority: int = 1
    is_active: bool = True


class AIConfigUpdate(BaseModel):
    """Request to update AI config"""
    name: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class AIConfigResponse(BaseModel):
    """AI Config response"""
    id: int
    provider: str
    name: str
    is_active: bool
    priority: int
    config: Dict[str, Any]  # API key is masked
    created_at: str
    updated_at: str


class AIConfigTestRequest(BaseModel):
    """Request to test AI config"""
    provider: str
    config_data: Dict[str, Any]


class AIConfigTestResponse(BaseModel):
    """Response from AI config test"""
    success: bool
    message: str
    latency_ms: Optional[int] = None


# Stats and Monitoring
class DailyStatsResponse(BaseModel):
    """Daily AI usage stats"""
    date: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    daily_limit_usd: float
    remaining_budget_usd: float
