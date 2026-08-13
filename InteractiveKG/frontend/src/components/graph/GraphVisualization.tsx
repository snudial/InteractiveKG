'use client';

import React, { useEffect, useRef, useState, useMemo } from 'react';
import cytoscape, { Core, NodeSingular, EdgeSingular } from 'cytoscape';
import dagre from 'cytoscape-dagre';
import coseBilkent from 'cytoscape-cose-bilkent';
import { GraphData, NodeData, RelationshipData, CytoscapeData } from '@/types/graph';
import { graphApi } from '@/lib/api';
import { NodeTooltip } from '@/components/ui/NodeTooltip';
import { RepresentativeNodeTooltip } from '@/components/ui/RepresentativeNodeTooltip';


cytoscape.use(dagre);
cytoscape.use(coseBilkent);

interface GraphVisualizationProps {
  data: GraphData;
  groupingAnalysis?: any;
  hierarchicalAnalysis?: any;
  viewMode?: 'unified' | 'semantic' | 'community' | 'structural'; 
  useHierarchicalView?: boolean;
  abstractionLevel?: number;
  panelViewMode?: 'community' | 'detailed'; 
  onNodeSelect?: (node: NodeData | null) => void;
  onRelationshipSelect?: (relationship: RelationshipData | null) => void;
  onNodeDoubleClick?: (node: NodeData) => void;
  onRelationshipDoubleClick?: (relationship: RelationshipData) => void;
  onVisibleNodesChange?: (nodeIds: string[]) => void; 
  highlightedNodes?: string[]; 
}


type ViewState = 'community' | 'detailed' | 'single_community';

interface CommunityNode {
  id: string;
  name: string;
  description: string;
  node_count: number;
  member_node_ids: string[];
  type: string;
  labels?: string[];
  properties?: Record<string, any>;
}

interface CommunityEdge {
  source: string;
  target: string;
  weight: number;
  edge_count: number;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  data,
  groupingAnalysis,
  hierarchicalAnalysis,
  viewMode = 'semantic',
  useHierarchicalView = false,
  abstractionLevel = 0,
  panelViewMode = 'community', 
  onNodeSelect,
  onRelationshipSelect,
  onNodeDoubleClick,
  onRelationshipDoubleClick,
  onVisibleNodesChange,
  highlightedNodes = [],
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedElement, setSelectedElement] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    position: { x: number; y: number };
    node?: NodeData;
    relationship?: RelationshipData;
  }>({
    visible: false,
    position: { x: 0, y: 0 },
  });

  
  const [viewState, setViewState] = useState<ViewState>('community');
  const [selectedCommunityId, setSelectedCommunityId] = useState<string | null>(null);
  const [legendCollapsed, setLegendCollapsed] = useState(false); 
  const [clickedCommunityNode, setClickedCommunityNode] = useState<{id: string, name: string, position: {x: number, y: number}} | null>(null); 
  const [singleCommunityData, setSingleCommunityData] = useState<GraphData | null>(null); 
  const [edgeWeightThresholds, setEdgeWeightThresholds] = useState<{
    strong: number;
    medium: number;
    weak: number;
  } | null>(null); 

  
  const supportsTwoStageView = useHierarchicalView &&
    hierarchicalAnalysis?.community_view &&
    hierarchicalAnalysis?.detailed_view &&
    abstractionLevel > 0;

  
  const analysisVersion = useMemo(() => {
    if (!hierarchicalAnalysis) return null;
    
    const level = hierarchicalAnalysis.abstraction_levels ?? 0;
    const source = hierarchicalAnalysis.analysis_metadata?.source || 'unknown';
    return `${level}_${source}`;
  }, [hierarchicalAnalysis?.abstraction_levels, hierarchicalAnalysis?.analysis_metadata?.source]);

  
  useEffect(() => {
    if (supportsTwoStageView && panelViewMode) {
      setViewState(panelViewMode);
      setSelectedCommunityId(null); 
      setSingleCommunityData(null); 
    }
  }, [panelViewMode, supportsTwoStageView]);

  
  useEffect(() => {
    if (supportsTwoStageView && viewState === 'community' && hierarchicalAnalysis?.community_view?.edges) {
      const thresholds = calculateEdgeWeightThresholds(hierarchicalAnalysis.community_view.edges);
      setEdgeWeightThresholds(thresholds);
    } else {
      
      setEdgeWeightThresholds(null);
    }
  }, [supportsTwoStageView, viewState, hierarchicalAnalysis?.community_view?.edges]);


  
  const getCurrentViewData = (): GraphData => {

    if (!supportsTwoStageView) {
      
      if (abstractionLevel === 0) {
        const filteredNodes = data.nodes.filter(node => !node.labels?.includes('Community'));
        return {
          nodes: filteredNodes,
          relationships: data.relationships
        };
      }
      return data; 
    }

    if (viewState === 'community') {
      
      return convertCommunityViewToGraphData(hierarchicalAnalysis.community_view);
    } else if (viewState === 'detailed') {
      
      return convertDetailedViewToGraphData(hierarchicalAnalysis.detailed_view);
    } else if (viewState === 'single_community' && singleCommunityData) {
      
      return singleCommunityData;
    }

    return data; 
  };

  
  const calculateEdgeWeightThresholds = (edges: any[]): {
    strong: number;
    medium: number;
    weak: number;
  } => {
    if (!edges || edges.length === 0) {
      return { strong: 5, medium: 3, weak: 2 }; 
    }

    
    const weights = edges.map(edge => edge.weight || 1).sort((a, b) => a - b);

    if (weights.length === 1) {
      
      const weight = weights[0];
      return { strong: weight, medium: weight, weak: weight };
    }

    
    const q1Index = Math.floor(weights.length * 0.25);
    const q2Index = Math.floor(weights.length * 0.50);
    const q3Index = Math.floor(weights.length * 0.75);

    const q1 = weights[q1Index];
    const q2 = weights[q2Index];
    const q3 = weights[q3Index];

    return {
      strong: q3,  
      medium: q2,  
      weak: q1     
    };
  };

  
  const convertCommunityViewToGraphData = (communityView: any): GraphData => {
    const nodes: NodeData[] = communityView.nodes.map((node: CommunityNode) => ({
      id: node.id,
      label: `${node.name}\n(${node.node_count} nodes)`,
      labels: node.labels || ['Community'],
      properties: {
        ...node.properties, 
        name: node.name,
        description: node.description,
        node_count: node.node_count,
        member_node_ids: node.member_node_ids,
        type: node.type || 'community'
      }
    }));

    const relationships: RelationshipData[] = communityView.edges.map((edge: CommunityEdge) => ({
      id: `${edge.source}-${edge.target}`,
      start_node_id: edge.source,
      end_node_id: edge.target,
      source_id: edge.source,  
      target_id: edge.target,  
      type: 'CONNECTS',
      properties: {
        weight: edge.weight,
        edge_count: edge.edge_count
      }
    }));

    return { nodes, relationships };
  };

  
  const convertDetailedViewToGraphData = (detailedView: any): GraphData => {
    let isFirstNode = true;
    const nodes: NodeData[] = detailedView.nodes.map((node: any) => {
      const convertedNode = {
        id: node.id,
        label: node.label,
        labels: node.labels,
        community_id: node.community_id, 
        community_name: node.community_name, 
        properties: {
          ...node.properties,
          community_id: node.community_id,
          community_name: node.community_name
        }
      } as any;

      
      if (isFirstNode) {
        isFirstNode = false;
      }

      return convertedNode;
    });

    const relationships: RelationshipData[] = detailedView.edges.map((edge: any) => ({
      id: edge.id || `${edge.source}-${edge.target}`,
      source_id: edge.source,
      target_id: edge.target,
      start_node_id: edge.source, 
      end_node_id: edge.target,   
      type: edge.type,
      properties: edge.properties
    }));

    return { nodes, relationships };
  };

  
  const convertSingleCommunityToGraphData = (detailedView: any, communityId: string): GraphData => {
    
    const communityNodes = detailedView.nodes.filter((node: any) =>
      node.community_id === communityId || node.community_name === communityId
    );

    const communityNodeIds = new Set(communityNodes.map((node: any) => node.id));

    
    const communityEdges = detailedView.edges.filter((edge: any) =>
      communityNodeIds.has(edge.source) && communityNodeIds.has(edge.target)
    );

    const nodes: NodeData[] = communityNodes.map((node: any) => ({
      id: node.id,
      label: node.label,
      labels: node.labels,
      properties: {
        ...node.properties,
        community_id: node.community_id,
        community_name: node.community_name
      }
    }));

    const relationships: RelationshipData[] = communityEdges.map((edge: any) => ({
      id: edge.id || `${edge.source}-${edge.target}`,
      start_node_id: edge.source,
      end_node_id: edge.target,
      source_id: edge.source,  
      target_id: edge.target,  
      type: edge.type,
      properties: edge.properties
    }));

    return { nodes, relationships };
  };

  
  const handleViewCommunityDetails = async (communityId: string) => {
    try {

      const communityDetail = await graphApi.communityDetail<any>(communityId, abstractionLevel);

      
      const nodes: NodeData[] = communityDetail.nodes.map((node: any) => ({
        id: node.id,
        label: node.label,
        labels: node.labels,
        properties: {
          ...node.properties,
          community_id: node.community_id,
          community_name: node.community_name
        }
      }));

      const relationships: RelationshipData[] = communityDetail.edges.map((edge: any) => ({
        id: edge.id || `${edge.source}-${edge.target}`,
        source_id: edge.source,
        target_id: edge.target,
        start_node_id: edge.source,
        end_node_id: edge.target,
        type: edge.type,
        properties: edge.properties
      }));

      
      const communityGraphData: GraphData = { nodes, relationships };

      
      setSingleCommunityData(communityGraphData);

      
      setSelectedCommunityId(communityId);
      setViewState('single_community');
      setClickedCommunityNode(null); 


    } catch (error) {
      console.error('Failed to load community details:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      alert(`Failed to load community details: ${errorMessage}`);
    }
  };

  
  const callbacksRef = useRef({
    onNodeSelect,
    onRelationshipSelect,
    onNodeDoubleClick,
    onRelationshipDoubleClick,
  });

  
  callbacksRef.current = {
    onNodeSelect,
    onRelationshipSelect,
    onNodeDoubleClick,
    onRelationshipDoubleClick,
  };

  
  const getNodeColor = (node: NodeData): string => {
    
    
    const typeValue = node.properties?.type;
    const isCommunityNode = node.labels?.includes('Community') ||
                           (typeof typeValue === 'string' && typeValue.toLowerCase().includes('community'));
    if (supportsTwoStageView && viewState === 'community' && isCommunityNode) {
      
      const communityName = node.properties.name || node.id;
      
      const colorMapping = hierarchicalAnalysis?.color_mapping?.level_0 || hierarchicalAnalysis?.color_mapping || {};
      const color = colorMapping[communityName];
      if (!color) {
        console.warn(`⚠️ No color found for community: ${communityName}`, { availableColors: Object.keys(colorMapping) });
      }
      return color || '#6B7280';
    }

    
    if (supportsTwoStageView && (viewState === 'detailed' || viewState === 'single_community')) {
      const communityName = (node as any).community_name || node.properties?.community_name;
      if (communityName) {
        const colorMapping = hierarchicalAnalysis?.color_mapping?.level_0 || hierarchicalAnalysis?.color_mapping || {};
        const color = colorMapping[communityName];
        if (!color) {
          console.warn(`⚠️ No color found for community: ${communityName} (node: ${node.id})`, { availableColors: Object.keys(colorMapping) });
        }
        return color || '#6B7280';
      } else {
        console.warn(`⚠️ No community_name found for node: ${node.id}`, { node });
      }
    }

    
    if (useHierarchicalView && hierarchicalAnalysis) {
      return getHierarchicalNodeColor(node, hierarchicalAnalysis, viewMode);
    }

    
    if (groupingAnalysis) {
      return getStandardNodeColor(node, groupingAnalysis);
    }

    return '#6B7280'; 
  };

  
  const getHierarchicalNodeColor = (node: NodeData, analysis: any, mode: string): string => {
    const nodeId = node.id;

    
    let groupData: Record<string, string[]> = {};
    const colorMapping: Record<string, string> = analysis.color_mapping || {};

    switch (mode) {
      case 'semantic':
        
        groupData = analysis.hierarchy?.level_0?.label_groups || {};
        
        for (const [groupName, nodeIds] of Object.entries(groupData)) {
          if (nodeIds.includes(nodeId)) {
            return colorMapping[groupName] || '#6B7280';
          }
        }
        break;
      case 'community':
        
        groupData = analysis.hierarchy?.community_overlay || {};
        
        for (const [communityId, nodeIds] of Object.entries(groupData)) {
          if (nodeIds.includes(nodeId)) {
            return colorMapping[`Community_${communityId}`] || '#6B7280';
          }
        }
        break;
      case 'structural':
        
        groupData = analysis.hierarchy?.structural_clusters || {};
        
        for (const [clusterId, nodeIds] of Object.entries(groupData)) {
          if (nodeIds.includes(nodeId)) {
            return colorMapping[`Cluster_${clusterId}`] || '#6B7280';
          }
        }
        break;
      default:
        groupData = analysis.hierarchy?.level_0?.label_groups || {};
        for (const [groupName, nodeIds] of Object.entries(groupData)) {
          if (nodeIds.includes(nodeId)) {
            return colorMapping[groupName] || '#6B7280';
          }
        }
    }

    
    const primaryLabel = node.labels[0] || 'Unknown';
    return colorMapping[primaryLabel] || '#6B7280';
  };

  
  const getStandardNodeColor = (node: NodeData, analysis: any): string => {
    
    if (analysis.abstraction_method) {
      const primaryLabel = node.labels[0] || 'Unknown';
      return analysis.color_mapping[primaryLabel] || '#6B7280';
    }

    
    if (!analysis.grouping_attribute) {
      return analysis?.default_color || '#6B7280';
    }

    const groupingAttr = analysis.grouping_attribute;
    let attrValue: string;

    if (groupingAttr === '_node_type') {
      attrValue = node.labels[0] || 'Unknown';
    } else {
      attrValue = String(node.properties[groupingAttr] || 'Unknown');
    }

    return analysis.color_mapping[attrValue] || analysis.default_color || '#6B7280';
  };

  
  
  
  const filterNodesForHierarchicalView = (
    nodes: NodeData[],
    analysis: any,
    mode: string,
    abstractionLevel: number
  ): NodeData[] => {

    
    
    return nodes;
  };

  const convertToCytoscapeData = (graphData: GraphData): CytoscapeData => {
    
    let filteredNodes: NodeData[];

    if (supportsTwoStageView) {
      
      filteredNodes = graphData.nodes;
    } else {
      
      filteredNodes = useHierarchicalView && hierarchicalAnalysis
        ? filterNodesForHierarchicalView(
            graphData.nodes,
            hierarchicalAnalysis,
            viewMode || 'semantic',
            abstractionLevel
          )
        : graphData.nodes;
    }

    

    
    if (onVisibleNodesChange) {
      const visibleNodeIds = filteredNodes.map(node => node.id);
      onVisibleNodesChange(visibleNodeIds);
    }

    const nodes = filteredNodes.map(node => ({
      data: {
        id: node.id,
        label: node.properties.display_name || node.properties.name || node.properties.displayName || node.labels.join(', ') || node.id,
        labels: node.labels,
        properties: node.properties,
        color: getNodeColor(node),
      },
    }));

    
    const visibleNodeIds = new Set(filteredNodes.map(node => node.id));
    const filteredRelationships = graphData.relationships.filter(rel =>
      visibleNodeIds.has(rel.start_node_id) && visibleNodeIds.has(rel.end_node_id)
    );

    const edges = filteredRelationships.map(rel => ({
      data: {
        id: rel.id,
        source: rel.start_node_id,
        target: rel.end_node_id,
        label: rel.type,
        type: rel.type,
        properties: rel.properties,
        weight: rel.properties?.weight || 1, 
        edge_count: rel.properties?.edge_count, 
      },
    }));

    return { nodes, edges };
  };

  
  useEffect(() => {
    if (!containerRef.current) return;


    const currentData = getCurrentViewData();
    const cytoscapeData = convertToCytoscapeData(currentData);

    // Cytoscape draws in raw pixels, so it ignores the root-font presentation
    // scaling from globals.css; mirror that scale here so node/edge labels grow
    // with the rest of the UI on large displays.
    const uiScale = (parseFloat(getComputedStyle(document.documentElement).fontSize) || 16) / 16;

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: [
        ...cytoscapeData.nodes,
        ...cytoscapeData.edges,
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#FFFFFF',
            'font-size': `${Math.round(12 * uiScale)}px`,
            'font-weight': 'bold',
            'width': `${Math.round(60 * uiScale)}px`,
            'height': `${Math.round(60 * uiScale)}px`,
            'border-width': '2px',
            'border-color': 'data(color)',
            'text-wrap': 'wrap',
            'text-max-width': `${Math.round(80 * uiScale)}px`,
            'text-outline-width': '2px',
            'text-outline-color': '#000000',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'background-color': '#EF4444',
            'border-color': '#DC2626',
            'border-width': '3px',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': (ele: any) => {
              return getEdgeWidth(ele);
            },
            'line-color': (ele: any) => {
              return getEdgeColor(ele);
            },
            'target-arrow-color': (ele: any) => {
              return getEdgeColor(ele);
            },
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': (ele: any) => {
              const edgeCount = ele.data('edge_count');
              const label = ele.data('label');

              
              if (supportsTwoStageView && viewState === 'community' && edgeCount) {
                return edgeCount === 1 ? '1 edge' : `${edgeCount} edges`;
              }

              
              if (label === 'CONNECTS' || label === 'connect') {
                return '';
              }

              return label || '';
            },
            'font-size': `${Math.round(10 * uiScale)}px`,
            'color': '#374151',
            'text-rotation': 'autorotate',
            'text-margin-y': -10 * uiScale,
            'opacity': (ele: any) => {
              return getEdgeOpacity(ele);
            },
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#EF4444',
            'target-arrow-color': '#EF4444',
            'width': 5,
            'opacity': 1,
          },
        },
      ],
      // cose-bilkent is a plugin layout, so its options are not covered by
      // cytoscape's built-in BaseLayoutOptions type.
      layout: {
        name: 'cose-bilkent',
        animate: true,
        animationDuration: 800,
        nodeDimensionsIncludeLabels: true,
        randomize: false,
        idealEdgeLength: 120,
        nodeRepulsion: 5000,
        nestingFactor: 0.05,
        gravity: 0.3,
        numIter: 3000,
        tile: true,
        tilingPaddingVertical: 15,
        tilingPaddingHorizontal: 15,
        nodeOverlap: 20,
        edgeElasticity: 0.45,
        gravityRangeCompound: 1.5,
        gravityCompound: 1.0,
        gravityRange: 3.8,
      } as any,
      wheelSensitivity: 0.2,
      minZoom: 0.1,
      maxZoom: 3,
    });

    // Same fit-after-settle for the initial layout run.
    cyRef.current.one('layoutstop', () => {
      cyRef.current?.fit(undefined, 40);
    });

    
    cyRef.current.on('tap', 'node', (event) => {
      const node = event.target;
      const nodeData = node.data();
      setSelectedElement(nodeData.id);

      
      setClickedCommunityNode(null);

      if (onNodeSelect) {
        const currentData = getCurrentViewData();
        const originalNode = currentData.nodes.find(n => n.id === nodeData.id);
        onNodeSelect(originalNode || null);
      }
    });

    cyRef.current.on('tap', 'edge', (event) => {
      const edge = event.target;
      const edgeData = edge.data();
      setSelectedElement(edgeData.id);
      
      if (onRelationshipSelect) {
        const originalRel = data.relationships.find(r => r.id === edgeData.id);
        onRelationshipSelect(originalRel || null);
      }
    });

    cyRef.current.on('tap', (event) => {
      if (event.target === cyRef.current) {
        setSelectedElement(null);
        setClickedCommunityNode(null); 
        onNodeSelect?.(null);
        onRelationshipSelect?.(null);
      }
    });

    cyRef.current.on('dblclick', 'node', (event) => {
      const node = event.target;
      const nodeData = node.data();


      if (!callbacksRef.current.onNodeDoubleClick) {
        console.warn('⚠️ onNodeDoubleClick callback not set');
        return;
      }

      
      const isCommunityNode = nodeData.labels?.includes('Community') || 
                             nodeData.properties?.type === 'community' ||
                             (typeof nodeData.properties?.type === 'string' && 
                              nodeData.properties.type.toLowerCase().includes('community'));

        
        const currentData = getCurrentViewData();
      let originalNode = currentData.nodes.find(n => n.id === nodeData.id);
      

      
      if (!originalNode) {
        originalNode = data.nodes.find(n => n.id === nodeData.id);
      }

      
      if (!originalNode && nodeData.properties?.name) {
        originalNode = data.nodes.find(n => 
          n.properties?.name === nodeData.properties.name ||
          n.properties?.displayName === nodeData.properties.name ||
          n.id === nodeData.properties.name
        );
      }

      
      if (isCommunityNode && !originalNode && hierarchicalAnalysis?.community_view) {
        const communityNode = hierarchicalAnalysis.community_view.nodes.find((n: any) => 
          n.id === nodeData.id || n.name === nodeData.id || n.name === nodeData.properties?.name
        );
        if (communityNode) {
          originalNode = {
            id: communityNode.id,
            label: communityNode.name || communityNode.label || nodeData.label || nodeData.id,
            labels: communityNode.labels || ['Community'],
            properties: {
              ...communityNode.properties,
              name: communityNode.name,
              description: communityNode.description,
              node_count: communityNode.node_count,
              member_node_ids: communityNode.member_node_ids,
              type: communityNode.type || 'community'
            }
          } as NodeData;
        }
      }

      
      if (!originalNode) {
        originalNode = {
          id: nodeData.id,
          label: nodeData.label || nodeData.properties?.name || nodeData.id,
          labels: nodeData.labels || [],
          properties: nodeData.properties || {}
        } as NodeData;
      }

        if (originalNode) {
          callbacksRef.current.onNodeDoubleClick(originalNode);
      } else {
        console.error('❌ Node not found for double-click:', {
          nodeId: nodeData.id,
          nodeLabels: nodeData.labels,
          nodeProperties: nodeData.properties,
          viewState,
          currentDataNodes: currentData.nodes.map(n => ({ id: n.id, labels: n.labels })),
          originalDataNodes: data.nodes.map(n => ({ id: n.id, labels: n.labels }))
        });
      }
    });

    
    cyRef.current.on('cxttap', 'node', (event) => {
      event.preventDefault();
      const node = event.target;
      const nodeData = node.data();
      setSelectedElement(nodeData.id);

      
      const typeValue = nodeData.properties?.type;
      const isCommunityNode = nodeData.labels?.includes('Community') ||
                             (typeof typeValue === 'string' && typeValue.toLowerCase().includes('community'));


      
      if (supportsTwoStageView && viewState === 'community' && isCommunityNode) {
        
        const position = node.renderedPosition();
        setClickedCommunityNode({
          id: nodeData.id,
          name: nodeData.properties.name || nodeData.label,
          position: { x: position.x, y: position.y }
        });
        return;
      }

      
      if (callbacksRef.current.onNodeSelect) {
        const originalNode = data.nodes.find(n => n.id === nodeData.id);
        callbacksRef.current.onNodeSelect(originalNode || null);
      }
    });

    
    cyRef.current.on('cxttap', 'edge', (event) => {
      event.preventDefault();
      const edge = event.target;
      const edgeData = edge.data();
      setSelectedElement(edgeData.id);

      if (callbacksRef.current.onRelationshipSelect) {
        const originalRel = data.relationships.find(r => r.id === edgeData.id);
        callbacksRef.current.onRelationshipSelect(originalRel || null);
      }
    });

    cyRef.current.on('dblclick', 'edge', (event) => {
      const edge = event.target;
      const edgeData = edge.data();


      if (!callbacksRef.current.onRelationshipDoubleClick) {
        console.warn('⚠️ onRelationshipDoubleClick callback not set');
        return;
      }

      
      const currentData = getCurrentViewData();
      let originalRel = currentData.relationships.find(r => r.id === edgeData.id);
      

      
      if (!originalRel) {
        originalRel = data.relationships.find(r => r.id === edgeData.id);
      }

      
      if (!originalRel && edgeData.source && edgeData.target) {
        originalRel = data.relationships.find(r => {
          const matchSource = r.start_node_id === edgeData.source ||
                             (r as any).source_id === edgeData.source ||
                             (r as any).source === edgeData.source;
          const matchTarget = r.end_node_id === edgeData.target ||
                             (r as any).target_id === edgeData.target ||
                             (r as any).target === edgeData.target;
          return matchSource && matchTarget;
        });
      }

      
      if (!originalRel && edgeData.source && edgeData.target) {
        originalRel = currentData.relationships.find(r => {
          const matchSource = r.start_node_id === edgeData.source || 
                             (r as any).source_id === edgeData.source ||
                             (r as any).source === edgeData.source;
          const matchTarget = r.end_node_id === edgeData.target || 
                             (r as any).target_id === edgeData.target ||
                             (r as any).target === edgeData.target;
          return matchSource && matchTarget;
        });
      }

      
      if (!originalRel && supportsTwoStageView && viewState === 'community' && hierarchicalAnalysis?.community_view) {
        const communityEdge = hierarchicalAnalysis.community_view.edges.find((e: any) => 
          e.source === edgeData.source && e.target === edgeData.target
        );
        if (communityEdge) {
          originalRel = {
            id: `${communityEdge.source}-${communityEdge.target}`,
            start_node_id: communityEdge.source,
            end_node_id: communityEdge.target,
            source_id: communityEdge.source,
            target_id: communityEdge.target,
            type: 'CONNECTS',
            properties: {
              weight: communityEdge.weight,
              edge_count: communityEdge.edge_count
            }
          } as RelationshipData;
        }
      }

      
      if (!originalRel && edgeData.source && edgeData.target) {
        originalRel = {
          id: edgeData.id || `${edgeData.source}-${edgeData.target}`,
          start_node_id: edgeData.source,
          end_node_id: edgeData.target,
          source_id: edgeData.source,
          target_id: edgeData.target,
          type: edgeData.type || 'RELATED',
          properties: edgeData.properties || {}
        } as RelationshipData;
      }

        if (originalRel) {
          callbacksRef.current.onRelationshipDoubleClick(originalRel);
      } else {
        console.error('❌ Relationship not found for double-click:', {
          edgeId: edgeData.id,
          source: edgeData.source,
          target: edgeData.target,
          type: edgeData.type,
          viewState,
          currentDataRelationships: currentData.relationships.map(r => ({ 
            id: r.id, 
            source: (r as any).start_node_id || (r as any).source_id || (r as any).source,
            target: (r as any).end_node_id || (r as any).target_id || (r as any).target
          })),
          originalDataRelationships: data.relationships.map(r => ({ 
            id: r.id, 
            source: (r as any).start_node_id || (r as any).source_id || (r as any).source,
            target: (r as any).end_node_id || (r as any).target_id || (r as any).target
          }))
        });
      }
    });

    
    cyRef.current.on('mouseover', 'node', (event) => {
      const node = event.target;
      const nodeData = node.data();
      const originalNode = data.nodes.find(n => n.id === nodeData.id);

      if (originalNode) {
        const renderedPosition = node.renderedPosition();
        setTooltip({
          visible: true,
          position: { x: renderedPosition.x, y: renderedPosition.y },
          node: originalNode,
        });
      }
    });

    cyRef.current.on('mouseover', 'edge', (event) => {
      const edge = event.target;
      const edgeData = edge.data();
      const originalRel = data.relationships.find(r => r.id === edgeData.id);

      if (originalRel) {
        const renderedMidpoint = edge.renderedMidpoint();
        setTooltip({
          visible: true,
          position: { x: renderedMidpoint.x, y: renderedMidpoint.y },
          relationship: originalRel,
        });
      }
    });

    cyRef.current.on('mouseout', 'node, edge', () => {
      setTooltip({
        visible: false,
        position: { x: 0, y: 0 },
      });
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [data, useHierarchicalView, analysisVersion, viewMode, abstractionLevel]);

  
  useEffect(() => {
    if (!cyRef.current) return;

    
    cyRef.current.edges().forEach((edge: any) => {
      edge.style('line-color', getEdgeColor(edge));
      edge.style('target-arrow-color', getEdgeColor(edge));
      edge.style('width', getEdgeWidth(edge));
      edge.style('opacity', getEdgeOpacity(edge));
    });
  }, [viewState, edgeWeightThresholds, supportsTwoStageView]);

  
  const getEdgeColor = (ele: any): string => {
    const weight = ele.data('weight') || 1;
    const edgeCount = ele.data('edge_count');

    if (supportsTwoStageView && viewState === 'community' && edgeWeightThresholds && edgeCount) {
      if (weight >= edgeWeightThresholds.strong) return '#EF4444';
      if (weight >= edgeWeightThresholds.medium) return '#F87171';
      if (weight >= edgeWeightThresholds.weak) return '#FCA5A5';
      return '#FECACA';
    }

    return '#6B7280';
  };

  const getEdgeWidth = (ele: any): number => {
    const weight = ele.data('weight') || 1;
    const edgeCount = ele.data('edge_count');

    if (supportsTwoStageView && viewState === 'community' && edgeWeightThresholds && edgeCount) {
      if (weight >= edgeWeightThresholds.strong) return 5;
      if (weight >= edgeWeightThresholds.medium) return 3.5;
      if (weight >= edgeWeightThresholds.weak) return 2.5;
      return 1.5;
    }

    return 2;
  };

  const getEdgeOpacity = (ele: any): number => {
    const weight = ele.data('weight') || 1;
    const edgeCount = ele.data('edge_count');

    if (supportsTwoStageView && viewState === 'community' && edgeWeightThresholds && edgeCount) {
      if (weight >= edgeWeightThresholds.strong) return 0.95;
      if (weight >= edgeWeightThresholds.medium) return 0.8;
      if (weight >= edgeWeightThresholds.weak) return 0.65;
      return 0.5;
    }

    return 0.7;
  };

  
  useEffect(() => {
    if (!cyRef.current) return;

    const currentData = getCurrentViewData();
    const cytoscapeData = convertToCytoscapeData(currentData);

    
    cyRef.current.elements().remove();

    
    cyRef.current.add([
      ...cytoscapeData.nodes,
      ...cytoscapeData.edges,
    ]);

    
    const relayout = cyRef.current.layout({
      name: 'cose-bilkent',
      animate: true,
      animationDuration: 800,
      nodeDimensionsIncludeLabels: true,
      randomize: false,
      idealEdgeLength: 120,
      nodeRepulsion: 5000,
    } as any);

    // Fit only after the animated layout has settled - fitting on a timer
    // captured mid-animation positions and left the graph huddled in a corner.
    relayout.one('layoutstop', () => {
      cyRef.current?.fit(undefined, 40);
    });
    relayout.run();

  }, [viewState, selectedCommunityId, analysisVersion, supportsTwoStageView, singleCommunityData, data, hierarchicalAnalysis, abstractionLevel]);

  return (
    <div className="relative w-full h-full">
      {}
      <div
        ref={containerRef}
        className="w-full h-full bg-gray-50/50"
      />

      {/* Community expansion popover */}
      {clickedCommunityNode && (
        <div
          className="absolute z-20 bg-white rounded-lg shadow-xl p-4 border-2 border-blue-500"
          style={{
            left: `${clickedCommunityNode.position.x + 50}px`,
            top: `${clickedCommunityNode.position.y - 50}px`,
            transform: 'translate(-50%, -50%)'
          }}
        >
          <div className="text-sm font-semibold text-gray-800 mb-2">
            {clickedCommunityNode.name}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleViewCommunityDetails(clickedCommunityNode.id)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              View Details
            </button>
            <button
              onClick={() => setClickedCommunityNode(null)}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {}
      <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 max-w-xs z-10 max-h-[calc(100%-2rem)] overflow-y-auto custom-scrollbar">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-800">
            {abstractionLevel === 0 ? 'Node Groups' :
             supportsTwoStageView && viewState === 'community' ? 'Communities' :
             supportsTwoStageView && viewState === 'single_community' ? `Community: ${selectedCommunityId}` :
             'Communities'}
          </h3>
          <button
            onClick={() => setLegendCollapsed(!legendCollapsed)}
            className="text-gray-500 hover:text-gray-700 text-xs"
          >
            {legendCollapsed ? '▼' : '▲'}
          </button>
        </div>

        {!legendCollapsed && (
          <>
            {}
            <div className="space-y-1.5">
              {}
              {abstractionLevel === 0 && hierarchicalAnalysis && (
                <>
                  <div className="text-xs text-gray-600 mb-2">
                    Grouped by: <span className="font-medium">Node Type</span>
                  </div>
                  {Object.entries(hierarchicalAnalysis.hierarchy?.level_0?.label_groups || {})
                    .filter(([groupName]) => groupName !== 'Community') 
                    .map(([groupName, nodeIds]: [string, any]) => {
                    const color = hierarchicalAnalysis.color_mapping?.[groupName] || '#6B7280';
                    return (
                      <div key={groupName} className="flex items-center gap-2 text-xs">
                        <div
                          className="w-4 h-4 rounded-full flex-shrink-0"
                          style={{ backgroundColor: color }}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-800 truncate">{groupName}</div>
                          <div className="text-gray-500">({nodeIds.length} nodes)</div>
                        </div>
                      </div>
                    );
                  })}
                </>
              )}

              {}
              {abstractionLevel > 0 && supportsTwoStageView && hierarchicalAnalysis && (
                <>
                  {viewState === 'community' && hierarchicalAnalysis.community_view?.nodes && (
                    <>
                      {}
                      <div className="text-xs text-gray-600 mb-2 font-medium">Communities:</div>
                      {hierarchicalAnalysis.community_view.nodes.map((community: any) => {
                        const color = hierarchicalAnalysis.color_mapping?.level_0?.[community.name] || '#6B7280';
                        return (
                          <div key={community.id} className="flex items-center gap-2 text-xs">
                            <div
                              className="w-4 h-4 rounded-full flex-shrink-0"
                              style={{ backgroundColor: color }}
                            />
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-gray-800 truncate">{community.name}</div>
                              <div className="text-gray-500">({community.node_count} nodes)</div>
                            </div>
                          </div>
                        );
                      })}

                      {}
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <div className="text-xs text-gray-600 mb-2 font-medium">Edge Strength:</div>
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-10 rounded flex-shrink-0" style={{ height: '5px', backgroundColor: '#EF4444' }}></div>
                            <span className="text-gray-700">Strong</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-8 rounded flex-shrink-0" style={{ height: '3.5px', backgroundColor: '#F87171' }}></div>
                            <span className="text-gray-700">Medium</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-6 rounded flex-shrink-0" style={{ height: '2.5px', backgroundColor: '#FCA5A5' }}></div>
                            <span className="text-gray-700">Weak</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 rounded flex-shrink-0" style={{ height: '1.5px', backgroundColor: '#FECACA' }}></div>
                            <span className="text-gray-700">Minimal</span>
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {(viewState === 'detailed' || viewState === 'single_community') && hierarchicalAnalysis.community_view?.nodes && (
                    <>
                      <div className="text-xs text-gray-600 mb-2">Nodes colored by community:</div>
                      {hierarchicalAnalysis.community_view.nodes.map((community: any) => {
                        const color = hierarchicalAnalysis.color_mapping?.level_0?.[community.name] || '#6B7280';
                        return (
                          <div key={community.id} className="flex items-center gap-2 text-xs">
                            <div
                              className="w-4 h-4 rounded-full flex-shrink-0"
                              style={{ backgroundColor: color }}
                            />
                            <div className="font-medium text-gray-800 truncate">{community.name}</div>
                          </div>
                        );
                      })}
                    </>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>

      {}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-2.5 text-xs">
        <div className="text-gray-700 font-medium">
          {supportsTwoStageView ? (
            <>
              {viewState === 'community'
                ? `${getCurrentViewData().nodes.length} Communities`
                : `${getCurrentViewData().nodes.length} Nodes`} · {getCurrentViewData().relationships.length} Edges
            </>
          ) : (
            <>
              {(() => {
                
                const filteredNodes = abstractionLevel === 0 
                  ? data.nodes.filter(node => !node.labels?.includes('Community'))
                  : data.nodes;
                return `${filteredNodes.length} Nodes · ${data.relationships.length} Edges`;
              })()}
            </>
          )}
        </div>
      </div>

      {}
      <NodeTooltip
        node={tooltip.node}
        relationship={tooltip.relationship}
        position={tooltip.position}
        visible={tooltip.visible}
      />
    </div>
  );
};
