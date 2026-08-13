'use client';

import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2, Edit3, Brain, GitBranch } from 'lucide-react';
import { NodeData, RelationshipData, ConnectedNodeInfo } from '@/types/graph';
import { SimplePropertyEditor } from './SimplePropertyEditor';
import { GraphAPI } from '@/lib/api';
import NodeExplanationPanel from './NodeExplanationPanel';
import { InsertNodeModal } from './InsertNodeModal';

interface PropertyPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  selectedNode?: NodeData | null;
  selectedRelationship?: RelationshipData | null;
  onSave?: (data: any) => void;
  onDelete?: () => void;
  onInsertNode?: () => void; 
  graphData?: { nodes: NodeData[]; relationships: RelationshipData[] }; 
  modalMode?: boolean;
  crudMode?: boolean; 
}

export const PropertyPanel: React.FC<PropertyPanelProps> = ({
  isOpen = true,
  onClose = () => {},
  selectedNode,
  selectedRelationship,
  onSave = () => {},
  onDelete,
  onInsertNode = () => {},
  graphData,
  modalMode = false,
  crudMode = false
}) => {
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<any>({});
  const [newPropertyKey, setNewPropertyKey] = useState('');
  const [newPropertyValue, setNewPropertyValue] = useState('');
  const [showInsertNodeModal, setShowInsertNodeModal] = useState(false);
  const selectedItem = selectedNode || selectedRelationship;
  const isNode = !!selectedNode;

  
  const getConnectedNodes = (nodeId: string): ConnectedNodeInfo[] => {
    if (!graphData || !nodeId) return [];

    const connectedNodes: ConnectedNodeInfo[] = [];

    
    graphData.relationships.forEach(rel => {
      let connectedNodeId: string | null = null;
      let relationshipType = rel.type;

      if (rel.start_node_id === nodeId) {
        connectedNodeId = rel.end_node_id;
      } else if (rel.end_node_id === nodeId) {
        connectedNodeId = rel.start_node_id;
        relationshipType = `${rel.type}(reverse)`;
      }

      if (connectedNodeId) {
        const connectedNode = graphData.nodes.find(n => n.id === connectedNodeId);
        if (connectedNode) {
          connectedNodes.push({
            id: connectedNode.id,
            name: connectedNode.properties?.displayName ||
                  connectedNode.properties?.name ||
                  connectedNode.properties?.title ||
                  connectedNode.id,
            type: connectedNode.labels?.[0] || 'Unknown Type',
            relationship_type: relationshipType,
            properties: connectedNode.properties
          });
        }
      }
    });

    return connectedNodes;
  };

  useEffect(() => {
    if (selectedItem) {
      setFormData({
        ...selectedItem,
        properties: { ...selectedItem.properties },
      });
      setEditMode(false);
    }
  }, [selectedItem]);

  const handlePropertyChange = (key: string, value: string) => {
    setFormData((prev: any) => ({
      ...prev,
      properties: {
        ...prev.properties,
        [key]: value,
      },
    }));
  };

  const handleAddProperty = () => {
    if (newPropertyKey && newPropertyValue) {
      handlePropertyChange(newPropertyKey, newPropertyValue);
      setNewPropertyKey('');
      setNewPropertyValue('');
    }
  };

  const handleRemoveProperty = (key: string) => {
    setFormData((prev: any) => {
      const newProperties = { ...prev.properties };
      delete newProperties[key];
      return {
        ...prev,
        properties: newProperties,
      };
    });
  };

  const handleSave = () => {
    onSave(formData);
    setEditMode(false);
  };

  const handleInsertNodeClick = () => {
    setShowInsertNodeModal(true);
  };

  const handleInsertNodeSuccess = () => {
    setShowInsertNodeModal(false);
    onInsertNode(); 
  };

  if (!isOpen || !selectedItem) {
    console.log('🚫 PropertyPanel not rendering:', { isOpen, hasSelectedItem: !!selectedItem });
    return null;
  }

  console.log('✅ PropertyPanel rendering:', { isOpen, selectedItem: selectedItem?.id });

  return (
    <div
      id="property-panel"
      className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl border-l border-gray-200 z-40 overflow-y-auto"
    >
      {}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          {isNode ? 'Node Properties' : 'Relationship Properties'}
        </h2>
        <div className="flex items-center space-x-2">
          {!editMode ? (
            <button
              onClick={() => setEditMode(true)}
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              title="Edit"
            >
              <Edit3 className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={handleSave}
              className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-md transition-colors"
              title="Save"
            >
              <Save className="h-4 w-4" />
            </button>
          )}
          {}
          {!isNode && selectedRelationship && (
            <button
              onClick={handleInsertNodeClick}
              className="p-2 text-purple-500 hover:text-purple-600 hover:bg-purple-50 rounded-md transition-colors"
              title="Insert node on relationship"
            >
              <GitBranch className="h-4 w-4" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-2 text-red-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
              title="Delete"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {}
      <div className="p-4 space-y-8">
        {}
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Property Information</h3>
          {editMode ? (
            <SimplePropertyEditor
              properties={formData.properties || {}}
              onChange={(properties) => setFormData((prev: typeof formData) => ({ ...prev, properties }))}
              isNode={isNode}
            />
          ) : (
            <div className="space-y-3">
              {Object.entries(formData.properties || {}).map(([key, value]) => (
                <div key={key} className="bg-white p-3 rounded border border-blue-200">
                  <div className="flex flex-col space-y-1">
                    <span className="text-sm font-semibold text-gray-800 capitalize">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm text-gray-900 break-words">
                      {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                    </span>
                  </div>
                </div>
              ))}
              {Object.keys(formData.properties || {}).length === 0 && (
                <div className="text-sm text-gray-600 italic bg-white p-3 rounded border border-blue-200">
                  No property information
                </div>
              )}
            </div>
          )}

          {}
          {isNode && selectedNode && (
            <div className="mt-6">
              <NodeExplanationPanel
                node={selectedNode}
                connectedNodes={getConnectedNodes(selectedNode.id)}
                className="border-t border-gray-200 pt-4"
              />
            </div>
          )}
        </div>
      </div>

      {}
      {selectedRelationship && graphData && (
        <InsertNodeModal
          isOpen={showInsertNodeModal}
          onClose={() => setShowInsertNodeModal(false)}
          onSuccess={handleInsertNodeSuccess}
          selectedRelationship={selectedRelationship}
          graphData={graphData}
        />
      )}
    </div>
  );
};

export default PropertyPanel;
