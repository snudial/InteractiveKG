from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
class NodeModel(BaseModel):

    id: Optional[str] = None
    labels: List[str] = Field(default_factory=list, description="Node labels")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
class RelationshipModel(BaseModel):

    id: Optional[str] = None
    type: str = Field(..., description="Relationship type")
    start_node_id: str = Field(..., description="Start node ID")
    end_node_id: str = Field(..., description="End node ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
class GraphDataModel(BaseModel):

    nodes: List[NodeModel] = Field(default_factory=list)
    relationships: List[RelationshipModel] = Field(default_factory=list)
class NodeCreateRequest(BaseModel):

    labels: List[str] = Field(..., description="Node labels")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
class NodeUpdateRequest(BaseModel):

    labels: Optional[List[str]] = None
    properties: Optional[Dict[str, Any]] = None
class RelationshipCreateRequest(BaseModel):

    type: str = Field(..., description="Relationship type")
    start_node_id: str = Field(..., description="Start node ID")
    end_node_id: str = Field(..., description="End node ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")
class RelationshipUpdateRequest(BaseModel):

    type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
class GraphSearchRequest(BaseModel):

    query: str = Field(..., description="Search query")
    node_labels: Optional[List[str]] = None
    relationship_types: Optional[List[str]] = None
    limit: int = Field(default=100, description="Maximum number of results")
class GraphSearchResponse(BaseModel):

    nodes: List[NodeModel]
    relationships: List[RelationshipModel]
    total_count: int