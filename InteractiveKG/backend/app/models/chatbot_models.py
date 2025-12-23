from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, Union
from enum import Enum
class ChatbotRole(str, Enum):

    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
class TestScenario(str, Enum):

    ACT_I = "act_1"
    ACT_II = "act_2"
class TestPhase(str, Enum):


    CASE1_INTRO = "case1_intro"
    CASE1_LLM_RESPONSE = "case1_llm_response"
    CASE1_EXPLORE_GRAPH = "case1_explore_graph"
    CASE1_IDENTIFY_ERRORS = "case1_identify_errors"
    CASE1_EDIT_CORRECT = "case1_edit_correct"
    CASE1_REQUERY_COMPARE = "case1_requery_compare"

    CASE2_INTRO = "case2_intro"
    CASE2_LLM_RESPONSE = "case2_llm_response"
    CASE2_EXPLORE_GRAPH = "case2_explore_graph"
    CASE2_IDENTIFY_ERRORS = "case2_identify_errors"
    CASE2_EDIT_CORRECT = "case2_edit_correct"
    CASE2_REQUERY_COMPARE = "case2_requery_compare"
class ChatMessage(BaseModel):

    role: ChatbotRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
class ChatbotState(BaseModel):

    session_id: str = Field(..., description="Session ID")
    current_scenario: Optional[TestScenario] = None
    current_phase: TestPhase = TestPhase.CASE1_INTRO
    user_role: str = "Knowledge Graph Researcher"
    messages: List[ChatMessage] = Field(default_factory=list)
    scenario_data_loaded: bool = False
    case1_completed: bool = False
    case2_completed: bool = False
    selected_domain: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
class ChatbotRequest(BaseModel):

    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    action: Optional[str] = None
class ChatbotResponse(BaseModel):

    session_id: str
    message: str
    current_phase: TestPhase
    current_scenario: Optional[TestScenario]
    ui_instructions: Dict[str, Any] = Field(default_factory=dict)
    advance_button: Optional[Dict[str, Any]] = Field(None, description="阶段推进按钮配置")
    data_source_selection_buttons: Optional[List[Dict[str, Any]]] = Field(None, description="数据源选择按钮")
    success: bool = True
    error: Optional[str] = None
class ScenarioLoadRequest(BaseModel):

    session_id: str
    scenario: TestScenario
class ScenarioLoadResponse(BaseModel):

    session_id: str
    scenario: TestScenario
    data_loaded: bool
    nodes_count: int
    relationships_count: int
    success: bool
    error: Optional[str] = None
class UserTestProgressRequest(BaseModel):

    session_id: str
    action: Literal["next_phase", "previous_phase", "reset", "complete_act"]
    phase: Optional[TestPhase] = None
class UserTestProgressResponse(BaseModel):

    session_id: str
    current_phase: TestPhase
    progress_percentage: float
    phase_description: str
    next_instructions: str
    success: bool
    error: Optional[str] = None
class AbstractionExplorationRequest(BaseModel):

    session_id: str
    abstraction_level: int = Field(..., ge=1, le=5, description="抽象级别 1-5")
    abstraction_mode: Literal["semantic", "structural", "community"] = Field(..., description="抽象模式")
    action: Literal["explore", "select", "compare"] = Field(..., description="探索动作")
class AbstractionExplorationResponse(BaseModel):

    session_id: str
    abstraction_level: int
    abstraction_mode: str
    exploration_data: Dict[str, Any]
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    success: bool
    error: Optional[str] = None
class IntegrationActionRequest(BaseModel):

    session_id: str
    action_type: Literal["highlight_nodes", "open_property_panel", "trigger_search", "load_data"]
    parameters: Dict[str, Any] = Field(default_factory=dict)
class IntegrationActionResponse(BaseModel):

    session_id: str
    action_type: str
    executed: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    success: bool
    error: Optional[str] = None