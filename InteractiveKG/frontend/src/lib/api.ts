/**
 * Client for the InteractiveKG backend API.
 *
 * The base URL comes from NEXT_PUBLIC_API_BASE_URL so the frontend can point at a
 * non-local backend without code changes; it falls back to the default dev backend.
 *
 * Two styles live here on purpose:
 *  - `GraphAPI` returns an {@link ApiResponse} envelope and never throws, which is what
 *    the graph editing UI expects — every call site branches on `response.error`.
 *  - `apiFetch` and the `graphApi`/`kgotApi`/`chatbotApi` helpers throw {@link ApiError},
 *    for panels that handle failures with try/catch.
 */

import type {
  ApiResponse,
  GraphData,
  NodeCreateRequest,
  NodeData,
  NodeExplanationRequest,
  NodeExplanationResponse,
  NodeUpdateRequest,
  RelationshipCreateRequest,
  RelationshipData,
} from '@/types/graph';

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '');

/** Build an absolute backend URL from an API path such as `/api/graph/data`. */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

/** Error carrying the HTTP status and, when available, the backend's `detail` message. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** Pull FastAPI's `detail` field out of an error body, when there is one. */
function readDetail(body: unknown): string | null {
  if (body && typeof body === 'object') {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  return null;
}

/**
 * Fetch an API path and parse the JSON body, raising {@link ApiError} on a non-2xx
 * response. `fallbackMessage` is used when the backend sends no `detail` field.
 */
export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
  fallbackMessage?: string,
): Promise<T> {
  const response = await fetch(apiUrl(path), init);

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      readDetail(body) ?? fallbackMessage ?? `Request to ${path} failed: ${response.statusText}`,
      response.status,
    );
  }

  return response.json() as Promise<T>;
}

/** JSON request init for a body-carrying method. */
function jsonInit(method: string, payload: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  };
}

/**
 * Run a request and convert both HTTP errors and network failures into an
 * {@link ApiResponse} envelope, so callers can branch on `.error` without try/catch.
 */
async function envelope<T>(
  path: string,
  init?: RequestInit,
  fallbackMessage?: string,
): Promise<ApiResponse<T>> {
  try {
    return { data: await apiFetch<T>(path, init, fallbackMessage) };
  } catch (error) {
    if (error instanceof ApiError) return { error: error.message };
    return { error: error instanceof Error ? error.message : 'Network request failed' };
  }
}

/* -------------------------------------------------------------------------- */
/* GraphAPI — envelope style, used by the graph editing UI                    */
/* -------------------------------------------------------------------------- */

export const GraphAPI = {
  /** Fetch every node and relationship currently stored. */
  getAllGraphData(): Promise<ApiResponse<GraphData>> {
    return envelope<GraphData>('/api/graph/data', undefined, 'Failed to load graph data');
  },

  /** Replace the stored graph with a bundled sample dataset. */
  loadSampleData(sampleData: unknown): Promise<ApiResponse<{ success: boolean; message: string; nodes_created: number; relationships_created: number }>> {
    return envelope('/api/graph/load-sample-data', jsonInit('POST', sampleData), 'Failed to load sample data');
  },

  /** Export the full graph as a JSON payload. */
  exportGraphData(): Promise<ApiResponse<GraphData>> {
    return envelope<GraphData>('/api/graph/export', undefined, 'Failed to export graph data');
  },

  /** Delete every node and relationship. */
  clearAllData(): Promise<ApiResponse<{ message: string }>> {
    return envelope('/api/graph/data', { method: 'DELETE' }, 'Failed to clear graph data');
  },

  /** Import a graph payload from an uploaded JSON file. */
  uploadJsonFile(file: File): Promise<ApiResponse<GraphData>> {
    const formData = new FormData();
    formData.append('file', file);
    return envelope<GraphData>('/api/graph/upload', { method: 'POST', body: formData }, 'Failed to upload file');
  },

  createNode(node: NodeCreateRequest): Promise<ApiResponse<NodeData>> {
    return envelope<NodeData>('/api/graph/nodes', jsonInit('POST', node), 'Failed to create node');
  },

  updateNode(nodeId: string, update: NodeUpdateRequest): Promise<ApiResponse<NodeData>> {
    return envelope<NodeData>(
      `/api/graph/nodes/${encodeURIComponent(nodeId)}`,
      jsonInit('PUT', update),
      'Failed to update node',
    );
  },

  deleteNode(nodeId: string): Promise<ApiResponse<{ message: string }>> {
    return envelope(
      `/api/graph/nodes/${encodeURIComponent(nodeId)}`,
      { method: 'DELETE' },
      'Failed to delete node',
    );
  },

  createRelationship(relationship: RelationshipCreateRequest): Promise<ApiResponse<RelationshipData>> {
    return envelope<RelationshipData>(
      '/api/graph/relationships',
      jsonInit('POST', relationship),
      'Failed to create relationship',
    );
  },

  deleteRelationship(relationshipId: string): Promise<ApiResponse<{ message: string }>> {
    return envelope(
      `/api/graph/relationships/${encodeURIComponent(relationshipId)}`,
      { method: 'DELETE' },
      'Failed to delete relationship',
    );
  },

  /** Suggested groupings over the current nodes, used to seed the abstraction UI. */
  getNodeGroupingAnalysis(): Promise<ApiResponse<Record<string, unknown>>> {
    return envelope('/api/graph/grouping-analysis', undefined, 'Failed to analyze node grouping');
  },

  /** Property/label schema summary, used to offer field suggestions in the editors. */
  getPropertySchemaAnalysis(): Promise<ApiResponse<Record<string, unknown>>> {
    return envelope('/api/graph/schema-analysis', undefined, 'Failed to analyze property schema');
  },

  /** Contextual semantic or reasoning explanation for a single node. */
  explainNode(request: NodeExplanationRequest): Promise<ApiResponse<NodeExplanationResponse>> {
    return envelope<NodeExplanationResponse>(
      '/api/graph/explain-node',
      jsonInit('POST', request),
      'Failed to explain node',
    );
  },
};

/* -------------------------------------------------------------------------- */
/* Throwing helpers, used by the KGOT and abstraction panels                   */
/* -------------------------------------------------------------------------- */

export const graphApi = {
  /** Expand a community node into its member nodes and relationships. */
  communityDetail<T>(communityId: string, abstractionLevel: number): Promise<T> {
    const params = new URLSearchParams({
      community_id: communityId,
      abstraction_level: String(abstractionLevel),
    });
    return apiFetch<T>(
      `/api/graph/community-detail?${params}`,
      undefined,
      'Failed to fetch community details',
    );
  },

  /** Run hierarchical (community-based) abstraction analysis over the stored graph. */
  hierarchicalAnalysis<T>(params: URLSearchParams): Promise<T> {
    return apiFetch<T>(`/api/graph/hierarchical-analysis?${params}`);
  },

  /** Delete every node and relationship in the backing store. */
  clear(): Promise<Response> {
    return fetch(apiUrl('/api/graph/data'), { method: 'DELETE' });
  },

  /** Import a graph payload, replacing the current contents. */
  import(payload: unknown): Promise<Response> {
    return fetch(apiUrl('/api/graph/import'), jsonInit('POST', payload));
  },
};

export const kgotApi = {
  /** Intelligent Solving mode: build a knowledge graph from the problem statement. */
  enhancedSolve<T>(payload: unknown): Promise<T> {
    return apiFetch<T>(
      '/api/kgot/enhanced-solve',
      jsonInit('POST', payload),
      'Intelligent problem solving failed',
    );
  },

  /** Internal Retrieval mode: answer using only the existing knowledge graph. */
  pureInternalRetrieve<T>(payload: unknown): Promise<T> {
    return apiFetch<T>(
      '/api/kgot/pure-internal-retrieve',
      jsonInit('POST', payload),
      'Pure internal retrieval failed',
    );
  },

  /** Load one of the bundled error datasets into the graph. */
  loadErrorData<T>(datasetId: string): Promise<T> {
    return apiFetch<T>(
      '/api/kgot/load-error-data',
      jsonInit('POST', { dataset_id: datasetId }),
      'Failed to load error dataset',
    );
  },
};

export const chatbotApi = {
  /** Fetch a bundled sample-data file by name. */
  sampleData<T>(filename: string): Promise<T> {
    return apiFetch<T>(`/api/chatbot/sample-data/${encodeURIComponent(filename)}`);
  },
};
