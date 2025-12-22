'use client';

import React from 'react';
import { HelpCircle } from 'lucide-react';
import { NodeData, RelationshipData } from '@/types/graph';

interface NodeTooltipProps {
  node?: NodeData;
  relationship?: RelationshipData;
  position: { x: number; y: number };
  visible: boolean;
  onExplainClick?: (node: NodeData) => void; 
}

export const NodeTooltip: React.FC<NodeTooltipProps> = ({
  node,
  relationship,
  position,
  visible,
  onExplainClick,
}) => {
  if (!visible || (!node && !relationship)) {
    return null;
  }

  const renderProperties = (properties: Record<string, any>) => {
    return Object.entries(properties)
      .filter(([key]) => key !== 'id') 
      .map(([key, value]) => (
        <div key={key} className="flex justify-between items-start space-x-3">
          <span className="text-gray-600 font-medium text-sm capitalize">
            {key.replace(/_/g, ' ')}:
          </span>
          <span className="text-gray-800 text-sm text-right flex-1">
            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
          </span>
        </div>
      ));
  };

  return (
    <div
      className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs pointer-events-none"
      style={{
        left: position.x + 10,
        top: position.y - 10,
        transform: position.x > window.innerWidth - 300 ? 'translateX(-100%)' : 'none',
      }}
    >
      {node && (
        <div className="space-y-2">
          <div className="border-b border-gray-200 pb-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-gray-900 text-sm">Node Details</div>
                <div className="text-xs text-gray-500 mt-1">
                  ID: {node.id.substring(0, 8)}...
                </div>
              </div>
              {onExplainClick && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onExplainClick(node);
                  }}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  title="AI解释：了解这个节点的含义和作用"
                >
                  <HelpCircle className="w-3 h-3" />
                  为什么？
                </button>
              )}
            </div>
          </div>
          
          {node.labels.length > 0 && (
            <div className="flex justify-between items-center">
              <span className="text-gray-600 font-medium text-sm">Labels:</span>
              <div className="flex flex-wrap gap-1">
                {node.labels.map((label, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                  >
                    {label}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          <div className="space-y-1">
            <div className="text-gray-700 font-medium text-sm">Properties:</div>
            {Object.keys(node.properties).length > 0 ? (
              <div className="space-y-1 pl-2">
                {renderProperties(node.properties)}
              </div>
            ) : (
              <div className="text-gray-500 text-sm italic pl-2">No properties</div>
            )}
          </div>
        </div>
      )}

      {relationship && (
        <div className="space-y-2">
          <div className="border-b border-gray-200 pb-2">
            <div className="font-semibold text-gray-900 text-sm">Relationship Details</div>
            <div className="text-xs text-gray-500 mt-1">
              ID: {relationship.id.substring(0, 8)}...
            </div>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-gray-600 font-medium text-sm">Type:</span>
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              {relationship.type}
            </span>
          </div>
          
          <div className="space-y-1">
            <div className="text-gray-700 font-medium text-sm">Properties:</div>
            {Object.keys(relationship.properties).length > 0 ? (
              <div className="space-y-1 pl-2">
                {renderProperties(relationship.properties)}
              </div>
            ) : (
              <div className="text-gray-500 text-sm italic pl-2">No properties</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
