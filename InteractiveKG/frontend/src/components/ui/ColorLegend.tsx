'use client';

import React from 'react';

interface ColorLegendProps {
  groupingAttribute: string | null;
  colorMapping: Record<string, string>;
  groups: Record<string, string[]>;
  isHierarchical?: boolean;
  hierarchicalMode?: 'unified' | 'semantic' | 'community' | 'structural';
  abstractionLevel?: number;
  totalNodes?: number;
  visibleNodes?: number;
  visibleNodeIds?: string[]; 
}

export const ColorLegend: React.FC<ColorLegendProps> = ({
  groupingAttribute,
  colorMapping,
  groups,
  isHierarchical = false,
  hierarchicalMode = 'unified',
  abstractionLevel = 3,
  totalNodes = 0,
  visibleNodes = 0,
  visibleNodeIds = [],
}) => {
  if (!groupingAttribute || Object.keys(colorMapping).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-3 text-sm">
        <div className="text-gray-600 font-medium mb-2">Node Coloring</div>
        <div className="flex items-center space-x-2">
          <div 
            className="w-3 h-3 rounded-full border border-gray-300"
            style={{ backgroundColor: '#6B7280' }}
          />
          <span className="text-gray-500">Default (no grouping)</span>
        </div>
      </div>
    );
  }

  
  const getColorMappingKey = (groupName: string, mode: string): string => {
    if (!isHierarchical) return groupName;

    switch (mode) {
      case 'unified':
        
        return groupName;
      case 'community':
        return `Community_${groupName}`;
      case 'structural':
        return `Cluster_${groupName}`;
      case 'semantic':
      default:
        return groupName;
    }
  };

  
  const buildVisibleGroups = (): Array<{groupName: string, color: string, nodeCount: number}> => {
    if (visibleNodeIds.length === 0) {
      
      return Object.entries(groups)
        .map(([groupKey, nodeIds]) => {
          const colorKey = getColorMappingKey(groupKey, hierarchicalMode || 'unified');
          const color = colorMapping[colorKey] || colorMapping[groupKey] || '#6B7280';

          return {
            groupName: groupKey,
            color,
            nodeCount: nodeIds.length
          };
        })
        .filter(group => group.nodeCount > 0)
        .sort((a, b) => a.groupName.localeCompare(b.groupName));
    }

    
    const visibleGroupCounts = new Map<string, number>();

    visibleNodeIds.forEach(nodeId => {
      
      for (const [groupKey, nodeIds] of Object.entries(groups)) {
        if (nodeIds.includes(nodeId)) {
          
          const displayName = groupKey;
          visibleGroupCounts.set(displayName, (visibleGroupCounts.get(displayName) || 0) + 1);
          break; 
        }
      }
    });

    
    const result = Array.from(visibleGroupCounts.entries())
      .map(([displayName, count]) => {
        const colorKey = getColorMappingKey(displayName, hierarchicalMode || 'unified');
        const color = colorMapping[colorKey] || colorMapping[displayName] || '#6B7280';

        return {
          groupName: displayName,
          color,
          nodeCount: count
        };
      })
      .filter(group => group.nodeCount > 0)
      .sort((a, b) => a.groupName.localeCompare(b.groupName));

    
    if (process.env.NODE_ENV === 'development') {
      console.log('ColorLegend Debug:', {
        mode: hierarchicalMode,
        isHierarchical,
        totalVisibleNodes: visibleNodeIds.length,
        resultGroups: result.map(g => `${g.groupName}(${g.nodeCount})`),
        originalGroups: Object.keys(groups).length,
        colorMappingKeys: Object.keys(colorMapping),
        colorMappingValues: colorMapping,
        groupsKeys: Object.keys(groups)
      });
    }

    return result;
  };

  const sortedGroups = buildVisibleGroups();

  return (
    <div className="bg-white rounded-lg shadow-lg p-3 text-sm max-w-xs">
      <div className="text-gray-700 font-medium mb-2">
        {isHierarchical ? (
          <div>
            <div className="text-purple-600">Hierarchical Abstraction (Level {abstractionLevel})</div>
            <div className="text-xs text-gray-500 mt-1">
              {hierarchicalMode === 'unified' && '🧠 Unified Cognitive Abstraction'}
              {hierarchicalMode === 'semantic' && 'Semantic Grouping'}
              {hierarchicalMode === 'community' && 'Community Detection'}
              {hierarchicalMode === 'structural' && 'Structural Clustering'}
            </div>
            {totalNodes > 0 && visibleNodes > 0 && (
              <div className="text-xs text-orange-600 mt-1 bg-orange-50 px-2 py-1 rounded">
                Showing {visibleNodes} / {totalNodes} nodes
                {totalNodes > visibleNodes && (
                  <span className="ml-1">({totalNodes - visibleNodes} hidden)</span>
                )}
              </div>
            )}
          </div>
        ) : (
          <span>分组依据: <span className="text-blue-600">{groupingAttribute}</span></span>
        )}
      </div>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {sortedGroups.length > 0 ? (
          sortedGroups.map(({ groupName, color, nodeCount }) => (
            <div key={groupName} className="flex items-center justify-between space-x-2">
              <div className="flex items-center space-x-2 flex-1 min-w-0">
                <div
                  className="w-3 h-3 rounded-full border border-gray-300 flex-shrink-0"
                  style={{ backgroundColor: color }}
                />
                <span className="text-gray-700 truncate" title={groupName}>
                  {groupName}
                </span>
              </div>
              <span className="text-gray-500 text-xs flex-shrink-0">
                ({nodeCount})
              </span>
            </div>
          ))
        ) : (
          <div className="text-gray-500 text-xs text-center py-2">
            当前视图中没有可显示的分组
          </div>
        )}
      </div>
    </div>
  );
};
