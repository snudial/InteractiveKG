'use client';

import React, { useState, useEffect } from 'react';
import { X, Plus, Save, ArrowRight } from 'lucide-react';
import { NodeData, RelationshipData } from '@/types/graph';
import { DynamicPropertyEditor } from './DynamicPropertyEditor';
import { GraphAPI } from '@/lib/api';

interface NodeCreateRequest {
  labels: string[];
  properties: Record<string, any>;
}

interface RelationshipCreateRequest {
  type: string;
  start_node_id: string;
  end_node_id: string;
  properties: Record<string, any>;
}

interface InsertNodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  selectedRelationship: RelationshipData;
  graphData: { nodes: NodeData[]; relationships: RelationshipData[] };
}

export const InsertNodeModal: React.FC<InsertNodeModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  selectedRelationship,
  graphData,
}) => {
  const [nodeLabels, setNodeLabels] = useState<string>('');
  const [nodeProperties, setNodeProperties] = useState<Record<string, string>>({});
  const [relationshipInheritance, setRelationshipInheritance] = useState<'inherit' | 'custom'>('inherit');
  const [firstRelType, setFirstRelType] = useState<string>('');
  const [firstRelProperties, setFirstRelProperties] = useState<Record<string, string>>({});
  const [secondRelType, setSecondRelType] = useState<string>('');
  const [secondRelProperties, setSecondRelProperties] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [schemaAnalysis, setSchemaAnalysis] = useState<any>(null);

  
  const startNode = graphData.nodes.find(n => n.id === selectedRelationship.start_node_id);
  const endNode = graphData.nodes.find(n => n.id === selectedRelationship.end_node_id);

  useEffect(() => {
    if (isOpen) {
      
      setNodeLabels('');
      setNodeProperties({});
      setRelationshipInheritance('inherit');
      setFirstRelType(selectedRelationship.type);
      setFirstRelProperties(selectedRelationship.properties || {});
      setSecondRelType(selectedRelationship.type);
      setSecondRelProperties(selectedRelationship.properties || {});
      
      
      loadSchemaAnalysis();
    }
  }, [isOpen, selectedRelationship]);

  const loadSchemaAnalysis = async () => {
    try {
      const response = await GraphAPI.getPropertySchemaAnalysis();
      if (!response.error) {
        setSchemaAnalysis(response.data);
      }
    } catch (error) {
      console.error('Failed to load schema analysis:', error);
    }
  };

  const getNodeDisplayName = (node: NodeData | undefined) => {
    if (!node) return 'Unknown';
    return node.properties.display_name || node.properties.name || node.labels.join(', ') || node.id.substring(0, 8);
  };

  const handleInsertNode = async () => {
    if (!nodeLabels.trim()) {
      alert('Please enter node labels');
      return;
    }

    setIsLoading(true);
    try {
      
      const nodeCreateRequest: NodeCreateRequest = {
        labels: nodeLabels.split(',').map(l => l.trim()).filter(l => l),
        properties: nodeProperties,
      };

      const nodeResponse = await GraphAPI.createNode(nodeCreateRequest);
      if (nodeResponse.error) {
        throw new Error(nodeResponse.error);
      }

      const newNode = nodeResponse.data!;

      
      const startNodeId = selectedRelationship.start_node_id || 
                         (selectedRelationship as any).source_id || 
                         (selectedRelationship as any).source;
      const endNodeId = selectedRelationship.end_node_id || 
                       (selectedRelationship as any).target_id || 
                       (selectedRelationship as any).target;

      if (!startNodeId || !endNodeId) {
        throw new Error('Relationship not found: Missing start or end node ID');
      }

      console.log('🔗 Inserting node on relationship:', {
        relationshipId: selectedRelationship.id,
        startNodeId,
        endNodeId,
        newNodeId: newNode.id,
        relationshipType: selectedRelationship.type
      });

      
      const firstRelRequest: RelationshipCreateRequest = {
        type: relationshipInheritance === 'inherit' ? selectedRelationship.type : firstRelType,
        start_node_id: startNodeId,
        end_node_id: newNode.id,
        properties: relationshipInheritance === 'inherit' ? (selectedRelationship.properties || {}) : firstRelProperties,
      };

      const firstRelResponse = await GraphAPI.createRelationship(firstRelRequest);
      if (firstRelResponse.error) {
        throw new Error(`Failed to create first relationship: ${firstRelResponse.error}`);
      }

      
      const secondRelRequest: RelationshipCreateRequest = {
        type: relationshipInheritance === 'inherit' ? selectedRelationship.type : secondRelType,
        start_node_id: newNode.id,
        end_node_id: endNodeId,
        properties: relationshipInheritance === 'inherit' ? (selectedRelationship.properties || {}) : secondRelProperties,
      };

      const secondRelResponse = await GraphAPI.createRelationship(secondRelRequest);
      if (secondRelResponse.error) {
        throw new Error(secondRelResponse.error);
      }

      
      const deleteResponse = await GraphAPI.deleteRelationship(selectedRelationship.id);
      if (deleteResponse.error) {
        throw new Error(deleteResponse.error);
      }

      
      onSuccess();
      handleClose();
    } catch (error) {
      console.error('Failed to insert node:', error);
      alert(`Failed to insert node: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setNodeLabels('');
    setNodeProperties({});
    setRelationshipInheritance('inherit');
    setFirstRelType('');
    setFirstRelProperties({});
    setSecondRelType('');
    setSecondRelProperties({});
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Insert Node on Relationship</h2>
          <button
            onClick={handleClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {}
        <div className="p-6 space-y-6">
          {}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Current Relationship</h3>
            <div className="flex items-center space-x-2 text-sm text-gray-700">
              <span className="font-medium">{getNodeDisplayName(startNode)}</span>
              <ArrowRight className="h-4 w-4" />
              <span className="px-2 py-1 bg-blue-100 rounded text-blue-800 font-medium">
                {selectedRelationship.type}
              </span>
              <ArrowRight className="h-4 w-4" />
              <span className="font-medium">{getNodeDisplayName(endNode)}</span>
            </div>
          </div>

          {}
          <div>
            <h3 className="text-base font-semibold text-gray-900 mb-3">New Node Configuration</h3>
            
            {}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Node Labels * (comma-separated)
              </label>
              <input
                type="text"
                value={nodeLabels}
                onChange={(e) => setNodeLabels(e.target.value)}
                placeholder="e.g., Person, Entity"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Node Properties
              </label>
              <DynamicPropertyEditor
                properties={nodeProperties}
                onChange={setNodeProperties}
                schema={schemaAnalysis}
                isNode={true}
              />
            </div>
          </div>

          {}
          <div>
            <h3 className="text-base font-semibold text-gray-900 mb-3">Relationship Configuration</h3>
            
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="inheritance"
                  value="inherit"
                  checked={relationshipInheritance === 'inherit'}
                  onChange={(e) => setRelationshipInheritance(e.target.value as 'inherit' | 'custom')}
                  className="mr-2"
                />
                <span className="text-sm">Inherit the original relationship type and properties</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="radio"
                  name="inheritance"
                  value="custom"
                  checked={relationshipInheritance === 'custom'}
                  onChange={(e) => setRelationshipInheritance(e.target.value as 'inherit' | 'custom')}
                  className="mr-2"
                />
                <span className="text-sm">Customize two new relationships</span>
              </label>
            </div>

            {}
            {relationshipInheritance === 'custom' && (
              <div className="mt-4 space-y-4">
                {}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">
                    {getNodeDisplayName(startNode)} → New Node
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Relationship Type</label>
                      <input
                        type="text"
                        value={firstRelType}
                        onChange={(e) => setFirstRelType(e.target.value)}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Properties</label>
                      <DynamicPropertyEditor
                        properties={firstRelProperties}
                        onChange={setFirstRelProperties}
                        schema={schemaAnalysis}
                        isNode={false}
                        compact={true}
                      />
                    </div>
                  </div>
                </div>

                {}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">
                    New Node → {getNodeDisplayName(endNode)}
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Relationship Type</label>
                      <input
                        type="text"
                        value={secondRelType}
                        onChange={(e) => setSecondRelType(e.target.value)}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Properties</label>
                      <DynamicPropertyEditor
                        properties={secondRelProperties}
                        onChange={setSecondRelProperties}
                        schema={schemaAnalysis}
                        isNode={false}
                        compact={true}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {}
        <div className="flex items-center justify-end space-x-3 p-4 border-t border-gray-200">
          <button
            onClick={handleClose}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleInsertNode}
            disabled={!nodeLabels.trim() || isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Inserting...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4 mr-1" />
                Insert Node
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
