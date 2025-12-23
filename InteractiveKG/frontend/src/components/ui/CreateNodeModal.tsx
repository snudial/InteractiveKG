'use client';

import React, { useState, useEffect } from 'react';
import { X, Plus, Save } from 'lucide-react';
import { DynamicPropertyEditor } from './DynamicPropertyEditor';
import { GraphAPI } from '@/lib/api';
import { NodeCreateRequest } from '@/types/graph';

interface CreateNodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (nodeData: NodeCreateRequest) => void;
}

export const CreateNodeModal: React.FC<CreateNodeModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [labels, setLabels] = useState('');
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
    const nodeData: NodeCreateRequest = {
      labels: labels.split(',').map(l => l.trim()).filter(l => l),
      properties: properties,
    };
    onSave(nodeData);
    handleClose();
  };

  const handleClose = () => {
    setLabels('');
    setProperties({});
    setNewPropertyKey('');
    setNewPropertyValue('');
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Create New Node</h2>
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
              Labels (comma-separated)
            </label>
            <input
              type="text"
              value={labels}
              onChange={(e) => setLabels(e.target.value)}
              placeholder="e.g., Person, Employee"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
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
              isNode={true}
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
            disabled={!labels.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Save className="h-4 w-4 inline mr-1" />
            Create Node
          </button>
        </div>
      </div>
    </div>
  );
};
