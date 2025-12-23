'use client';

import React from 'react';

interface RepresentativeNodeTooltipProps {
  node: any;
  groupInfo?: {
    groupName: string;
    totalNodes: number;
    hiddenNodes: number;
    representativeScore: number;
  };
  isVisible: boolean;
  position: { x: number; y: number };
}

export const RepresentativeNodeTooltip: React.FC<RepresentativeNodeTooltipProps> = ({
  node,
  groupInfo,
  isVisible,
  position,
}) => {
  if (!isVisible || !node) return null;

  return (
    <div
      className="absolute z-50 bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-sm max-w-xs"
      style={{
        left: position.x + 10,
        top: position.y - 10,
        pointerEvents: 'none',
      }}
    >
      <div className="space-y-2">
        {}
        <div>
          <div className="font-semibold text-gray-900">
            {node.properties?.name || node.properties?.displayName || node.id}
          </div>
          <div className="text-xs text-gray-500">
            Type: {node.labels?.join(', ') || 'Unknown'}
          </div>
        </div>

        {}
        {groupInfo && (
          <div className="border-t pt-2">
            <div className="text-xs text-purple-600 font-medium mb-1">
              🏷️ Representative Node
            </div>
            <div className="space-y-1 text-xs text-gray-600">
              <div>Group: {groupInfo.groupName}</div>
              <div>Represents {groupInfo.totalNodes} nodes</div>
              {groupInfo.hiddenNodes > 0 && (
                <div className="text-orange-600">
                  {groupInfo.hiddenNodes} related nodes hidden
                </div>
              )}
              <div className="text-blue-600">
                Importance Score: {groupInfo.representativeScore.toFixed(2)}
              </div>
            </div>
          </div>
        )}

        {}
        {node.properties && Object.keys(node.properties).length > 0 && (
          <div className="border-t pt-2">
            <div className="text-xs text-gray-500 font-medium mb-1">属性:</div>
            <div className="space-y-1">
              {Object.entries(node.properties)
                .slice(0, 3) 
                .map(([key, value]) => (
                  <div key={key} className="text-xs">
                    <span className="text-gray-500">{key}:</span>{' '}
                    <span className="text-gray-700">
                      {String(value).length > 30 
                        ? String(value).substring(0, 30) + '...' 
                        : String(value)
                      }
                    </span>
                  </div>
                ))}
              {Object.keys(node.properties).length > 3 && (
                <div className="text-xs text-gray-400">
                  ... 还有 {Object.keys(node.properties).length - 3} 个属性
                </div>
              )}
            </div>
          </div>
        )}

        {}
        <div className="border-t pt-2 text-xs text-gray-400">
          💡 双击展开查看分组详细节点
        </div>
      </div>
    </div>
  );
};
