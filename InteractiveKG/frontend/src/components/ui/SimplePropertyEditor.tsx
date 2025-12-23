import React, { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

interface SimplePropertyEditorProps {
  properties: Record<string, any>;
  onChange: (properties: Record<string, any>) => void;
  isNode: boolean;
}

export const SimplePropertyEditor: React.FC<SimplePropertyEditorProps> = ({
  properties,
  onChange,
  isNode
}) => {
  const [selectedProperty, setSelectedProperty] = useState('');
  const [propertyValue, setPropertyValue] = useState('');
  const [customPropertyName, setCustomPropertyName] = useState('');
  const [isAddingNew, setIsAddingNew] = useState(false);

  
  const getAvailableProperties = () => {
    return Object.keys(properties).filter(key => key !== 'id');
  };

  
  const handlePropertySelect = (value: string) => {
    if (value === '__NEW_PROPERTY__') {
      setIsAddingNew(true);
      setSelectedProperty('');
      setPropertyValue('');
      setCustomPropertyName('');
    } else {
      setIsAddingNew(false);
      setSelectedProperty(value);
      setPropertyValue(properties[value] || '');
      setCustomPropertyName('');
    }
  };

  
  const applyChange = () => {
    const finalKey = isAddingNew ? customPropertyName : selectedProperty;
    if (!finalKey.trim()) return;

    const updatedProperties = {
      ...properties,
      [finalKey]: propertyValue
    };

    onChange(updatedProperties);
    
    
    setSelectedProperty('');
    setPropertyValue('');
    setCustomPropertyName('');
    setIsAddingNew(false);
  };

  
  const deleteProperty = () => {
    if (!selectedProperty) return;

    const updatedProperties = { ...properties };
    delete updatedProperties[selectedProperty];
    
    onChange(updatedProperties);
    
    
    setSelectedProperty('');
    setPropertyValue('');
  };

  const availableProperties = getAvailableProperties();

  return (
    <div className="space-y-4">
      {}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="space-y-3">
          {}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Property
            </label>
            <select
              value={isAddingNew ? '__NEW_PROPERTY__' : selectedProperty}
              onChange={(e) => handlePropertySelect(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
            >
              <option value="">-- Select a property to edit --</option>
              {availableProperties.map(key => (
                <option key={key} value={key}>
                  {key.replace(/_/g, ' ')}
                </option>
              ))}
              <option value="__NEW_PROPERTY__">+ Add New Property</option>
            </select>
          </div>

          {}
          {isAddingNew && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                New Property Name
              </label>
              <input
                type="text"
                value={customPropertyName}
                onChange={(e) => setCustomPropertyName(e.target.value)}
                placeholder="Enter new property name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
              />
            </div>
          )}

          {}
          {(selectedProperty || (isAddingNew && customPropertyName)) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Property Value
              </label>
              <input
                type="text"
                value={propertyValue}
                onChange={(e) => setPropertyValue(e.target.value)}
                placeholder="Enter property value"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
              />
            </div>
          )}

          {}
          {(selectedProperty || (isAddingNew && customPropertyName)) && (
            <div className="flex space-x-2 pt-2">
              <button
                onClick={applyChange}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              >
                {isAddingNew ? 'Add Property' : 'Apply Changes'}
              </button>
              {selectedProperty && !isAddingNew && (
                <button
                  onClick={deleteProperty}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors flex items-center"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Delete Property
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {}
      <div className="pt-2">
        <button
          onClick={() => {
            
            setSelectedProperty('');
            setPropertyValue('');
            setCustomPropertyName('');
            setIsAddingNew(false);
          }}
          className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors flex items-center justify-center"
        >
          <Plus className="h-5 w-5 mr-2" />
          Continue editing other properties
        </button>
      </div>
    </div>
  );
};
