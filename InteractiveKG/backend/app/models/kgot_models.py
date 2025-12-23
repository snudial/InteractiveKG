from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
class ExplanationType(str, Enum):

    SEMANTIC = "semantic"
    REASONING = "reasoning"
class ConnectedNodeInfo(BaseModel):

    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型")
    relationship_type: str = Field(..., description="关系类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
class NodeExplanationRequest(BaseModel):

    node_id: str = Field(..., description="要解释的节点ID")
    node_properties: Dict[str, Any] = Field(..., description="节点属性对象")
    connected_nodes: List[ConnectedNodeInfo] = Field(default_factory=list, description="相连节点信息数组")
    explanation_type: ExplanationType = Field(default=ExplanationType.SEMANTIC, description="解释类型")
    abstraction_level: Optional[int] = Field(default=3, description="抽象级别", ge=1, le=5)
    abstraction_mode: Optional[str] = Field(default="semantic", description="抽象模式")
class NodeExplanationResponse(BaseModel):

    success: bool = Field(..., description="是否成功")
    explanation: str = Field(..., description="解释内容")
    explanation_type: ExplanationType = Field(..., description="解释类型")
    node_id: str = Field(..., description="节点ID")
    execution_time: float = Field(..., description="执行时间（秒）")
    error: Optional[str] = Field(None, description="错误信息")
    cached: bool = Field(default=False, description="是否来自缓存")
class KGOTEnhancedSolveRequest(BaseModel):

    problem: str = Field(..., description="问题描述")
    learn_from_solution: bool = Field(default=True, description="是否从解决方案中学习")
    use_hierarchical_view: bool = Field(default=False, description="是否使用层级视图")
    abstraction_level: int = Field(default=3, description="抽象级别", ge=1, le=5)
    abstraction_mode: str = Field(default="semantic", description="抽象模式")
class KGOTPureRetrieveRequest(BaseModel):

    query: str = Field(..., description="查询内容")
    abstraction_level: int = Field(default=3, description="抽象级别", ge=1, le=5)
    abstraction_mode: str = Field(default="semantic", description="抽象模式")
class KGOTResponse(BaseModel):

    success: bool = Field(..., description="是否成功")
    answer: str = Field(..., description="回答内容")
    execution_time: float = Field(..., description="执行时间（秒）")
    error: Optional[str] = Field(None, description="错误信息")
    kg_updates: int = Field(default=0, description="知识图谱更新数量")
    retrieved_context: Optional[str] = Field(None, description="检索到的上下文")