import React, { useState } from 'react';
import { HelpCircle, Loader2, ChevronDown, ChevronUp, Brain, Search, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { GraphAPI } from '@/lib/api';
import { NodeData, RelationshipData, ExplanationType, NodeExplanationResponse, ConnectedNodeInfo } from '@/types/graph';

interface NodeExplanationPanelProps {
  node?: NodeData;
  connectedNodes?: ConnectedNodeInfo[];
  className?: string;
  modalMode?: boolean;
  analysisMode?: 'understanding' | 'anomaly'; 
}

const NodeExplanationPanel: React.FC<NodeExplanationPanelProps> = ({
  node,
  connectedNodes = [],
  className = '',
  modalMode = false,
  analysisMode = 'understanding'
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [explanation, setExplanation] = useState<NodeExplanationResponse | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [explanationType, setExplanationType] = useState<ExplanationType>('semantic');
  const [error, setError] = useState<string | null>(null);

  const handleExplain = async (type: ExplanationType) => {
    if (!node) {
      setError('Please select a node first for explanation');
      return;
    }

    setIsLoading(true);
    setError(null);
    setExplanationType(type);

    try {
      const response = await GraphAPI.explainNode({
        node_id: node.id,
        node_properties: node.properties,
        connected_nodes: connectedNodes,
        explanation_type: type,
        abstraction_level: 3,
        abstraction_mode: 'semantic'
      });

      if (response.error) {
        setError(response.error);
        setExplanation(null);
      } else if (response.data) {
        setExplanation(response.data);
        setIsExpanded(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Explanation generation failed');
      setExplanation(null);
    } finally {
      setIsLoading(false);
    }
  };

  const getNodeDisplayName = (node: NodeData): string => {
    return (
      node.properties?.displayName ||
      node.properties?.name ||
      node.properties?.title ||
      node.id
    );
  };

  const formatExecutionTime = (time: number): string => {
    return time < 1 ? `${Math.round(time * 1000)}ms` : `${time.toFixed(2)}s`;
  };

  return (
    <div
      id="node-explanation-panel"
      className={`${modalMode ? '' : 'bg-white border border-gray-200 rounded-lg shadow-sm'} ${className}`}
    >
      {}
      {!modalMode && (
        <div className="px-4 py-3 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-800">AI Explanation Assistant</h3>
            <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded-full">
              Why?
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            {node ? `Understand the semantic meaning and generation principles of node "${getNodeDisplayName(node)}"` : 'Select a node for explanation'}
          </p>
        </div>
      )}

      {}
      {modalMode && (
        <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <h4 className="font-semibold text-gray-800">
              {analysisMode === 'anomaly' ? 'Anomaly Node Analysis' : 'Deep Node Explanation'}
            </h4>
          </div>
          <p className="text-sm text-gray-600">
            {analysisMode === 'anomaly'
              ? 'Click suspicious nodes in the graph to analyze whether they are hallucinations or erroneous data using AI'
              : 'Click any node in the graph to deeply understand AI grouping and reasoning basis'
            }
          </p>
          {node && (
            <p className="text-sm text-blue-700 mt-2 font-medium">
              Currently Selected: {getNodeDisplayName(node)}
            </p>
          )}
        </div>
      )}

      {}
      <div className="p-4 space-y-3">
        <div className="flex gap-2">
          <button
            onClick={() => handleExplain('semantic')}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading && explanationType === 'semantic' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            Semantic Analysis
          </button>

          <button
            onClick={() => handleExplain('reasoning')}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading && explanationType === 'reasoning' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Brain className="w-4 h-4" />
            )}
            Reasoning Process
          </button>
        </div>

        {}
        {connectedNodes.length > 0 && (
          <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
            <span className="font-medium">Related Connections: </span>
            {connectedNodes.slice(0, 3).map((conn, idx) => (
              <span key={conn.id}>
                {idx > 0 && ', '}
                {conn.name}({conn.relationship_type})
              </span>
            ))}
            {connectedNodes.length > 3 && ` and ${connectedNodes.length - 3} more nodes`}
          </div>
        )}
      </div>

      {}
      {(explanation || error) && (
        <div className="border-t border-gray-100">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              {explanation?.success ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600" />
              )}
              <span className="font-medium text-gray-800">
                {explanation?.success ? 'Explanation Result' : 'Explanation Failed'}
              </span>
              {explanation?.cached && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                  Cached
                </span>
              )}
            </div>
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {isExpanded && (
            <div className="px-4 pb-4">
              {explanation?.success ? (
                <div className="space-y-3">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="text-sm text-gray-800 leading-relaxed prose prose-sm max-w-none prose-headings:text-gray-900 prose-strong:text-gray-900 prose-p:text-gray-800 prose-li:text-gray-800">
                      <ReactMarkdown>{explanation.explanation}</ReactMarkdown>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>Duration: {formatExecutionTime(explanation.execution_time)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      {explanation.explanation_type === 'semantic' ? (
                        <Search className="w-3 h-3" />
                      ) : (
                        <Brain className="w-3 h-3" />
                      )}
                      <span>
                        {explanation.explanation_type === 'semantic' ? 'Semantic Analysis' : 'Reasoning Process'}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="text-sm text-red-800">
                    {error || explanation?.error || 'Explanation generation failed'}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NodeExplanationPanel;
