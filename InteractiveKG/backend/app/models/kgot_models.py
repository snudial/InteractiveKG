from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
class ExplanationType(str, Enum):

    SEMANTIC = "semantic"
    REASONING = "reasoning"
class ConnectedNodeInfo(BaseModel):

    id: str = Field(..., description="Node ID")
    name: str = Field(..., description="Node name")
    type: str = Field(..., description="Node type")
    relationship_type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
class NodeExplanationRequest(BaseModel):

    node_id: str = Field(..., description="ID of the node to explain")
    node_properties: Dict[str, Any] = Field(..., description="Node property object")
    connected_nodes: List[ConnectedNodeInfo] = Field(default_factory=list, description="Connected node info list")
    explanation_type: ExplanationType = Field(default=ExplanationType.SEMANTIC, description="Explanation type")
    abstraction_level: Optional[int] = Field(default=3, description="Abstraction level", ge=1, le=5)
    abstraction_mode: Optional[str] = Field(default="semantic", description="Abstraction mode")
class NodeExplanationResponse(BaseModel):

    success: bool = Field(..., description="Whether the call succeeded")
    explanation: str = Field(..., description="Explanation text")
    explanation_type: ExplanationType = Field(..., description="Explanation type")
    node_id: str = Field(..., description="Node ID")
    execution_time: float = Field(..., description="Execution time in seconds")
    error: Optional[str] = Field(None, description="Error message")
    cached: bool = Field(default=False, description="Whether the result came from cache")
class KGOTEnhancedSolveRequest(BaseModel):

    problem: str = Field(..., description="Problem statement")
    learn_from_solution: bool = Field(default=True, description="Whether to learn from the solution")
    use_hierarchical_view: bool = Field(default=False, description="Whether to use the hierarchical view")
    abstraction_level: int = Field(default=3, description="Abstraction level", ge=1, le=5)
    abstraction_mode: str = Field(default="semantic", description="Abstraction mode")
class KGOTPureRetrieveRequest(BaseModel):

    query: str = Field(..., description="Query text")
    abstraction_level: int = Field(default=3, description="Abstraction level", ge=1, le=5)
    abstraction_mode: str = Field(default="semantic", description="Abstraction mode")
class KGOTResponse(BaseModel):

    success: bool = Field(..., description="Whether the call succeeded")
    answer: str = Field(..., description="Answer text")
    execution_time: float = Field(..., description="Execution time in seconds")
    error: Optional[str] = Field(None, description="Error message")
    kg_updates: int = Field(default=0, description="Number of knowledge graph updates")
    retrieved_context: Optional[str] = Field(None, description="Retrieved context")