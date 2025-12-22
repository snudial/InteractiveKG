

export interface NodeData {
  id: string;
  labels: string[];
  properties: Record<string, any>;
}

export interface RelationshipData {
  id: string;
  type: string;
  start_node_id: string;
  end_node_id: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: NodeData[];
  relationships: RelationshipData[];
}

export interface NodeCreateRequest {
  labels: string[];
  properties: Record<string, any>;
}

export interface NodeUpdateRequest {
  labels?: string[];
  properties?: Record<string, any>;
}

export interface RelationshipCreateRequest {
  type: string;
  start_node_id: string;
  end_node_id: string;
  properties: Record<string, any>;
}

export interface RelationshipUpdateRequest {
  type?: string;
  properties?: Record<string, any>;
}


export interface CytoscapeNode {
  data: {
    id: string;
    label: string;
    labels: string[];
    properties: Record<string, any>;
  };
  position?: {
    x: number;
    y: number;
  };
}

export interface CytoscapeEdge {
  data: {
    id: string;
    source: string;
    target: string;
    label: string;
    type: string;
    properties: Record<string, any>;
  };
}

export interface CytoscapeData {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
}

export interface GraphStats {
  nodeCount: number;
  relationshipCount: number;
  nodeLabels: string[];
  relationshipTypes: string[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}


export type ExplanationType = 'semantic' | 'reasoning';

export interface ConnectedNodeInfo {
  id: string;
  name: string;
  type: string;
  relationship_type: string;
  properties: Record<string, any>;
}

export interface NodeExplanationRequest {
  node_id: string;
  node_properties: Record<string, any>;
  connected_nodes: ConnectedNodeInfo[];
  explanation_type: ExplanationType;
  abstraction_level?: number;
  abstraction_mode?: string;
}

export interface NodeExplanationResponse {
  success: boolean;
  explanation: string;
  explanation_type: ExplanationType;
  node_id: string;
  execution_time: number;
  error?: string;
  cached: boolean;
}
