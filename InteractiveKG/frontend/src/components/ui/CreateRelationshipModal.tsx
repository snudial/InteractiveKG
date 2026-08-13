'use client';

import React, { useState, useEffect } from 'react';
import { X, Plus, Save } from 'lucide-react';
import { NodeData } from '@/types/graph';
import { DynamicPropertyEditor } from './DynamicPropertyEditor';
import { GraphAPI } from '@/lib/api';

interface RelationshipCreateRequest {
  type: string;
  start_node_id: string;
  end_node_id: string;
  properties: Record<string, any>;
}

interface CreateRelationshipModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (relationshipData: RelationshipCreateRequest) => void;
  nodes: NodeData[];
  preselectedStartNode?: NodeData;
  preselectedEndNode?: NodeData;
}

export const CreateRelationshipModal: React.FC<CreateRelationshipModalProps> = ({
  isOpen,
  onClose,
  onSave,
  nodes,
  preselectedStartNode,
  preselectedEndNode,
}) => {
  const [relationshipType, setRelationshipType] = useState('');
  const [startNodeId, setStartNodeId] = useState(preselectedStartNode?.id || '');
  const [endNodeId, setEndNodeId] = useState(preselectedEndNode?.id || '');
  const [properties, setProperties] = useState<Record<string, string>>({});
  const [newPropertyKey, setNewPropertyKey] = useState('');
  const [newPropertyValue, setNewPropertyValue] = useState('');
  const [schemaAnalysis, setSchemaAnalysis] = useState<any>(null);

  
  useEffect(() => {
    if (isOpen && !schemaAnalysis) {
      loadSchemaAnalysis();
    }
  }, [isOpen]);

  const loadSchemaAnalysis = async () => {
    try {
      const response = await GraphAPI.getPropertySchemaAnalysis();
      if (response.data) {
        setSchemaAnalysis(response.data);
      }
    } catch (error) {
      console.warn('Failed to load schema analysis:', error);
    }
  };

  const handleAddProperty = () => {
    if (newPropertyKey && newPropertyValue) {
      setProperties(prev => ({
        ...prev,
        [newPropertyKey]: newPropertyValue,
      }));
      setNewPropertyKey('');
      setNewPropertyValue('');
    }
  };

  const handleRemoveProperty = (key: string) => {
    setProperties(prev => {
      const newProps = { ...prev };
      delete newProps[key];
      return newProps;
    });
  };

  const handleSave = () => {
    if (!relationshipType || !startNodeId || !endNodeId) {
      return;
    }

    const relationshipData: RelationshipCreateRequest = {
      type: relationshipType,
      start_node_id: startNodeId,
      end_node_id: endNodeId,
      properties: properties,
    };
    
    onSave(relationshipData);
    handleClose();
  };

  const handleClose = () => {
    setRelationshipType('');
    setStartNodeId(preselectedStartNode?.id || '');
    setEndNodeId(preselectedEndNode?.id || '');
    setProperties({});
    setNewPropertyKey('');
    setNewPropertyValue('');
    onClose();
  };

  const getNodeDisplayName = (node: NodeData) => {
    return node.properties.name || node.labels.join(', ') || node.id.substring(0, 8);
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Create New Relationship</h2>
          <button
            onClick={handleClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {}
        <div className="p-4 space-y-4">
          {}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Relationship Type *
            </label>
            <input
              type="text"
              value={relationshipType}
              onChange={(e) => setRelationshipType(e.target.value)}
              placeholder="e.g., WORKS_FOR, KNOWS, RELATED_TO"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Node *
            </label>
            <select
              value={startNodeId}
              onChange={(e) => setStartNodeId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select start node</option>
              {nodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {getNodeDisplayName(node)}
                </option>
              ))}
            </select>
          </div>

          {}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To Node *
            </label>
            <select
              value={endNodeId}
              onChange={(e) => setEndNodeId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select end node</option>
              {nodes.filter(node => node.id !== startNodeId).map((node) => (
                <option key={node.id} value={node.id}>
                  {getNodeDisplayName(node)}
                </option>
              ))}
            </select>
          </div>

          {}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Properties
            </label>

            <DynamicPropertyEditor
              properties={properties}
              onChange={setProperties}
              schema={schemaAnalysis}
              isNode={false}
            />
          </div>
        </div>

        {}
        <div className="flex items-center justify-end space-x-3 p-4 border-t border-gray-200">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!relationshipType || !startNodeId || !endNodeId}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Save className="h-4 w-4 inline mr-1" />
            Create Relationship
          </button>
        </div>
      </div>
    </div>
  );
};
