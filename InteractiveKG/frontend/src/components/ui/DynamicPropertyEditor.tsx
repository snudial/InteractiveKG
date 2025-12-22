'use client';

import React, { useState, useEffect } from 'react';
import { Plus, X, ChevronDown } from 'lucide-react';

interface PropertySchema {
  type: string;
  examples: string[];
  frequency: number;
}

interface SchemaAnalysis {
  node_schema: {
    labels: string[];
    properties: Record<string, PropertySchema>;
  };
  relationship_schema: {
    types: string[];
    properties: Record<string, PropertySchema>;
  };
}

interface DynamicPropertyEditorProps {
  properties: Record<string, any>;
  onChange: (properties: Record<string, any>) => void;
  schema?: SchemaAnalysis;
  isNode?: boolean;
  compact?: boolean; 
}

export const DynamicPropertyEditor: React.FC<DynamicPropertyEditorProps> = ({
  properties,
  onChange,
  schema,
  isNode = true,
  compact = false,
}) => {
  const [newPropertyKey, setNewPropertyKey] = useState('');
  const [newPropertyValue, setNewPropertyValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const getAvailableProperties = () => {
    if (!schema) return [];
    
    const schemaProps = isNode 
      ? schema.node_schema.properties 
      : schema.relationship_schema.properties;
    
    return Object.keys(schemaProps).filter(key => !(key in properties));
  };

  const getPropertySuggestions = (key: string): string[] => {
    if (!schema) return [];
    
    const schemaProps = isNode 
      ? schema.node_schema.properties 
      : schema.relationship_schema.properties;
    
    const propSchema = schemaProps[key];
    return propSchema?.examples || [];
  };

  const handlePropertyChange = (key: string, value: string) => {
    const updatedProperties = { ...properties, [key]: value };
    onChange(updatedProperties);
  };

  const handleRemoveProperty = (key: string) => {
    const updatedProperties = { ...properties };
    delete updatedProperties[key];
    onChange(updatedProperties);
  };

  const handleAddProperty = () => {
    if (newPropertyKey && newPropertyValue) {
      const updatedProperties = { ...properties, [newPropertyKey]: newPropertyValue };
      onChange(updatedProperties);
      setNewPropertyKey('');
      setNewPropertyValue('');
      setShowSuggestions(false);
    }
  };

  const handleSuggestionSelect = (key: string) => {
    setNewPropertyKey(key);
    setShowSuggestions(false);
  };

  const availableProperties = getAvailableProperties();

  return (
    <div className={compact ? "space-y-3" : "space-y-6"}>
      {}
      <div className={compact ? "space-y-2" : "space-y-4"}>
        {Object.entries(properties)
          .filter(([key]) => key !== 'id')
          .map(([key, value]) => {
            const suggestions = getPropertySuggestions(key);
            return (
              <div key={key} className={compact ? "bg-white p-2 rounded border border-gray-200" : "bg-white p-4 rounded-lg border border-gray-200 shadow-sm"}>
                <div className={compact ? "flex items-center justify-between mb-1" : "flex items-center justify-between mb-3"}>
                  <label className={compact ? "text-xs font-medium text-gray-700 capitalize" : "text-sm font-semibold text-gray-800 capitalize"}>
                    {key.replace(/_/g, ' ')}
                  </label>
                  <button
                    onClick={() => handleRemoveProperty(key)}
                    className="p-1 text-red-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <X className={compact ? "h-3 w-3" : "h-4 w-4"} />
                  </button>
                </div>

                <div className={compact ? "space-y-1" : "space-y-2"}>
                  <input
                    type="text"
                    value={String(value)}
                    onChange={(e) => handlePropertyChange(key, e.target.value)}
                    className={compact ? "w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900" : "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"}
                    placeholder={`Enter ${key.replace(/_/g, ' ')}`}
                  />

                  {}
                  {suggestions.length > 0 && (
                    <div className="bg-gray-50 border border-gray-200 rounded-md p-2">
                      <div className="text-xs font-medium text-gray-600 mb-2">
                        Common values:
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {suggestions.slice(0, 6).map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => handlePropertyChange(key, suggestion)}
                            className="px-2 py-1 text-xs bg-white border border-gray-200 rounded hover:bg-blue-50 hover:border-blue-300 transition-colors text-gray-700"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
      </div>

      {}
      <div className="bg-green-50 p-4 rounded-lg border border-green-200">
        <div className="text-sm font-semibold text-gray-800 mb-4">Add New Property</div>

        <div className="space-y-4">
          {}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Property Name</label>
            <div className="flex">
              <input
                type="text"
                placeholder="Enter property name"
                value={newPropertyKey}
                onChange={(e) => setNewPropertyKey(e.target.value)}
                onFocus={() => setShowSuggestions(true)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
              />
              {availableProperties.length > 0 && (
                <button
                  onClick={() => setShowSuggestions(!showSuggestions)}
                  className="px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <ChevronDown className="h-4 w-4 text-gray-500" />
                </button>
              )}
            </div>
            
            {}
            {showSuggestions && availableProperties.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-md shadow-sm p-2 mt-2">
                <div className="text-xs font-medium text-gray-600 mb-2">
                  Available property suggestions:
                </div>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {availableProperties.map((prop) => {
                    const propInfo = isNode
                      ? schema?.node_schema.properties[prop]
                      : schema?.relationship_schema.properties[prop];

                    return (
                      <button
                        key={prop}
                        onClick={() => handleSuggestionSelect(prop)}
                        className="w-full text-left px-2 py-1 hover:bg-gray-50 focus:bg-gray-50 rounded text-sm"
                      >
                        <div className="font-medium text-gray-900">{prop.replace(/_/g, ' ')}</div>
                        <div className="text-xs text-gray-500">
                          Used {propInfo?.frequency || 0} times
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Property Value</label>
            <input
              type="text"
              placeholder="Enter property value"
              value={newPropertyValue}
              onChange={(e) => setNewPropertyValue(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
            />
          </div>

          {}
          <button
            onClick={handleAddProperty}
            disabled={!newPropertyKey || !newPropertyValue}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Plus className="h-4 w-4 inline mr-2" />
            Add Property
          </button>
        </div>
      </div>
    </div>
  );
};
