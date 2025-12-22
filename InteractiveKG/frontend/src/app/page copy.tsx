'use client';

import React, { useState, useEffect } from 'react';
import { FileUploadButton } from '@/components/upload/FileUploadButton';
import { GraphVisualization } from '@/components/graph/GraphVisualization';
import { PropertyPanel } from '@/components/ui/PropertyPanel';
import { CreateNodeModal } from '@/components/ui/CreateNodeModal';
import { CreateRelationshipModal } from '@/components/ui/CreateRelationshipModal';
import { ColorLegend } from '@/components/ui/ColorLegend';
import { HierarchicalAbstractionPanel } from '@/components/ui/HierarchicalAbstractionPanel';
import EnhancedKGOTPanel from '@/components/ui/EnhancedKGOTPanel';
import ChatbotPanel from '@/components/ui/ChatbotPanel';
import { GraphAPI } from '@/lib/api';
import { GraphData, NodeData, RelationshipData, NodeCreateRequest } from '@/types/graph';
import { Download, RefreshCw, Trash2, Database, Plus, Link } from 'lucide-react';

export default function Home() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], relationships: [] });
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [selectedRelationship, setSelectedRelationship] = useState<RelationshipData | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCreateRelModalOpen, setIsCreateRelModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [groupingAnalysis, setGroupingAnalysis] = useState<any>(null);
  const [hierarchicalAnalysis, setHierarchicalAnalysis] = useState<any>(null);
  const [useHierarchicalView, setUseHierarchicalView] = useState(false);
  const [hierarchicalViewMode] = useState<'unified'>('unified'); 
  const [hierarchicalAbstractionLevel, setHierarchicalAbstractionLevel] = useState(1);
  const [showFullView, setShowFullView] = useState(false);
  const [visibleNodeIds, setVisibleNodeIds] = useState<string[]>([]);

  
  const [highlightedNodes, setHighlightedNodes] = useState<string[]>([]);
  const [activeKGOTTab, setActiveKGOTTab] = useState<'solve' | 'retrieve'>('retrieve');

  
  const getHierarchicalGroups = (analysis: any, mode: string): Record<string, string[]> => {
    if (!analysis?.hierarchy) return {};

    
    if (mode === 'unified') {
      return analysis.hierarchy.level_0?.label_groups || {};
    }

    
    switch (mode) {
      case 'semantic':
        return analysis.hierarchy.level_0?.label_groups ||
               analysis.hierarchy.level_0?.domain_core_groups || {};
      case 'community':
        return analysis.hierarchy.community_overlay || {};
      case 'structural':
        return analysis.hierarchy.structural_clusters || {};
      default:
        return analysis.hierarchy.level_0?.label_groups || {};
    }
  };

  
  const calculateVisibleNodes = (): number => {
    if (!useHierarchicalView || !hierarchicalAnalysis) {
      return graphData.nodes.length;
    }

    
    if (hierarchicalAbstractionLevel === 1) {
      return graphData.nodes.length;
    }

    const groupData = getHierarchicalGroups(hierarchicalAnalysis, hierarchicalViewMode);
    if (Object.keys(groupData).length === 0) {
      return graphData.nodes.length;
    }

    
    const nodesPerGroup = Math.max(1, Math.floor(6 - hierarchicalAbstractionLevel));
    let totalVisible = 0;

    Object.values(groupData).forEach(nodeIds => {
      if (nodeIds.length > 0) {
        totalVisible += Math.min(nodesPerGroup, nodeIds.length);
      }
    });

    return Math.max(totalVisible, Math.floor(graphData.nodes.length / Math.max(1, hierarchicalAbstractionLevel)));
  };

  
  useEffect(() => {
    if (hierarchicalAnalysis && !useHierarchicalView) {
      console.log('Auto-switching to hierarchical view');
      setUseHierarchicalView(true);
    }
  }, [hierarchicalAnalysis]);

  
  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGroupingAnalysis = async () => {
    try {
      const response = await GraphAPI.getNodeGroupingAnalysis();
      if (response.error) {
        console.warn('Failed to load grouping analysis:', response.error);
        setGroupingAnalysis(null);
      } else {
        setGroupingAnalysis(response.data);
      }
    } catch (err) {
      console.warn('Failed to load grouping analysis:', err);
      setGroupingAnalysis(null);
    }
  };

  const loadGraphData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await GraphAPI.getAllGraphData();

      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setGraphData(response.data);
        
        await loadGroupingAnalysis();
      } else {
        setError('No data received from server');
      }
    } catch (err) {
      console.error('Failed to load graph data:', err);
      setError(`Failed to load graph data: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadSuccess = async (data: GraphData) => {
    setGraphData(data);
    setError(null);
    
    await loadGroupingAnalysis();
  };

  const handleUploadError = (error: string) => {
    setError(error);
  };

  const handleNodeSelect = (node: NodeData | null) => {
    setSelectedNode(node);
    setSelectedRelationship(null);
    setIsPanelOpen(!!node);
  };

  const handleRelationshipSelect = (relationship: RelationshipData | null) => {
    setSelectedRelationship(relationship);
    setSelectedNode(null);
    setIsPanelOpen(!!relationship);
  };

  const handleSave = async (data: any) => {
    setIsLoading(true);
    setError(null);

    try {
      if (selectedNode) {
        
        const response = await GraphAPI.updateNode(selectedNode.id, {
          labels: data.labels,
          properties: data.properties,
        });

        if (response.error) {
          setError(response.error);
        } else {
          
          await loadGraphData();
          setIsPanelOpen(false);
        }
      } else if (selectedRelationship) {
        
        
        console.log('Update relationship:', data);
        setIsPanelOpen(false);
      }
    } catch (err) {
      setError('Failed to save changes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('确定要删除选中的项目吗？此操作不可撤销。')) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (selectedNode) {
        const response = await GraphAPI.deleteNode(selectedNode.id);
        if (response.error) {
          setError(response.error);
        } else {
          await loadGraphData();
          setSelectedNode(null);
          setIsPanelOpen(false);
        }
      } else if (selectedRelationship) {
        const response = await GraphAPI.deleteRelationship(selectedRelationship.id);
        if (response.error) {
          setError(response.error);
        } else {
          await loadGraphData();
          setSelectedRelationship(null);
          setIsPanelOpen(false);
        }
      }
    } catch (err) {
      setError('Failed to delete item');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (confirm('确定要清空所有数据吗？此操作不可撤销。')) {
      setIsLoading(true);
      try {
        const response = await GraphAPI.clearAllData();
        if (response.error) {
          setError(response.error);
        } else {
          setGraphData({ nodes: [], relationships: [] });
          setSelectedNode(null);
          setSelectedRelationship(null);
          setIsPanelOpen(false);
        }
      } catch (err) {
        setError('Failed to clear data');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleExport = async () => {
    try {
      const response = await GraphAPI.exportGraphData();
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        const dataStr = JSON.stringify(response.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'graph_data.json';
        link.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      setError('Failed to export data');
    }
  };

  const handleCreateNode = async (nodeData: NodeCreateRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await GraphAPI.createNode(nodeData);
      if (response.error) {
        setError(response.error);
      } else {
        await loadGraphData();
        setIsCreateModalOpen(false);
      }
    } catch (err) {
      setError('Failed to create node');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateRelationship = async (relationshipData: any) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await GraphAPI.createRelationship(relationshipData);
      if (response.error) {
        setError(response.error);
      } else {
        await loadGraphData();
        setIsCreateRelModalOpen(false);
      }
    } catch (err) {
      setError('Failed to create relationship');
    } finally {
      setIsLoading(false);
    }
  };

  
  const handleHighlightNodes = (nodeIds: string[]) => {
    setHighlightedNodes(nodeIds);
    
  };

  const handleOpenPropertyPanel = (nodeId: string) => {
    const node = graphData.nodes.find(n => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
      setIsPanelOpen(true);
    }
  };

  const handleTriggerKGOTSearch = (query: string, tab: 'solve' | 'retrieve') => {
    setActiveKGOTTab(tab);
    
    console.log('Triggering KGOT search:', { query, tab });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-semibold text-gray-900">
                知识图谱管理系统
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              <FileUploadButton
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />

              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="inline-flex items-center px-3 py-2 border border-green-300 shadow-sm text-sm leading-4 font-medium rounded-md text-green-700 bg-white hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Node
              </button>

              <button
                onClick={() => setIsCreateRelModalOpen(true)}
                disabled={!graphData || graphData.nodes.length < 2}
                className="inline-flex items-center px-3 py-2 border border-purple-300 shadow-sm text-sm leading-4 font-medium rounded-md text-purple-700 bg-white hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Link className="h-4 w-4 mr-2" />
                Create Relationship
              </button>

              <button
                onClick={loadGraphData}
                disabled={isLoading}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                刷新
              </button>

              <button
                onClick={handleExport}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Download className="h-4 w-4 mr-2" />
                导出
              </button>

              <button
                onClick={handleClearAll}
                className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                清空
              </button>
            </div>
          </div>
        </div>
      </header>

      {}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
          {}
          <div className="lg:col-span-1">
            <div className="space-y-6" style={{ height: '700px' }}>
              {}
              <HierarchicalAbstractionPanel
                onAnalysisChange={setHierarchicalAnalysis}
                onAbstractionLevelChange={setHierarchicalAbstractionLevel}
                onFullViewChange={setShowFullView}
                isLoading={isLoading}
              />

              {}
              <div className="flex-1">
                <EnhancedKGOTPanel
                  onDataUpdate={loadGraphData}
                  useHierarchicalView={useHierarchicalView}
                  hierarchicalAbstractionLevel={hierarchicalAbstractionLevel}
                  hierarchicalViewMode={hierarchicalViewMode}
                  activeTab={activeKGOTTab}
                />
              </div>
            </div>
          </div>

          {}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow" style={{ height: '700px' }}>
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">
                  知识图谱可视化
                </h2>
              </div>
              <div className="p-6 h-full">
                <div style={{ height: '600px' }} className="relative">
                  <GraphVisualization
                    data={graphData}
                    groupingAnalysis={groupingAnalysis}
                    hierarchicalAnalysis={hierarchicalAnalysis}
                    viewMode={hierarchicalViewMode}
                    useHierarchicalView={useHierarchicalView}
                    abstractionLevel={showFullView ? 1 : hierarchicalAbstractionLevel}
                    onNodeSelect={handleNodeSelect}
                    onRelationshipSelect={handleRelationshipSelect}
                    onVisibleNodesChange={setVisibleNodeIds}
                    highlightedNodes={highlightedNodes}
                  />

                  {}
                  {process.env.NODE_ENV === 'development' && (
                    <div className="absolute bottom-4 right-4 bg-black bg-opacity-75 text-white p-2 rounded text-xs z-20">
                      <div>showFullView: {showFullView.toString()}</div>
                      <div>abstractionLevel: {showFullView ? 1 : hierarchicalAbstractionLevel}</div>
                      <div>useHierarchicalView: {useHierarchicalView.toString()}</div>
                      <div>hasHierarchicalAnalysis: {!!hierarchicalAnalysis}</div>
                      <div>nodeCount: {graphData.nodes.length}</div>
                      <div>visibleNodes: {showFullView ? graphData.nodes.length : calculateVisibleNodes()}</div>
                    </div>
                  )}

                  {}
                  {(useHierarchicalView ? hierarchicalAnalysis : groupingAnalysis) && (
                    <div className="absolute top-4 left-4 z-10">
                      <ColorLegend
                        groupingAttribute={
                          useHierarchicalView
                            ? '层级抽象'
                            : (groupingAnalysis?.grouping_attribute || null)
                        }
                        colorMapping={
                          useHierarchicalView
                            ? (hierarchicalAnalysis?.color_mapping || {})
                            : (groupingAnalysis?.color_mapping || {})
                        }
                        groups={
                          useHierarchicalView
                            ? (getHierarchicalGroups(hierarchicalAnalysis, hierarchicalViewMode) || {})
                            : (groupingAnalysis?.groups || {})
                        }
                        isHierarchical={useHierarchicalView}
                        hierarchicalMode={hierarchicalViewMode}
                        abstractionLevel={showFullView ? 1 : hierarchicalAbstractionLevel}
                        totalNodes={graphData.nodes.length}
                        visibleNodes={showFullView ? graphData.nodes.length : calculateVisibleNodes()}
                        visibleNodeIds={visibleNodeIds}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {}
          <div className="lg:col-span-1">
            <div style={{ height: '700px' }}>
              <ChatbotPanel
                onDataUpdate={loadGraphData}
                onHighlightNodes={handleHighlightNodes}
                onOpenPropertyPanel={handleOpenPropertyPanel}
                onTriggerKGOTSearch={handleTriggerKGOTSearch}
                currentGraphData={graphData}
              />
            </div>
          </div>
        </div>
      </main>

      {}
      <PropertyPanel
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        selectedNode={selectedNode}
        selectedRelationship={selectedRelationship}
        onSave={handleSave}
        onDelete={handleDelete}
        graphData={graphData}
      />

      {}
      <CreateNodeModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSave={handleCreateNode}
      />

      {}
      <CreateRelationshipModal
        isOpen={isCreateRelModalOpen}
        onClose={() => setIsCreateRelModalOpen(false)}
        onSave={handleCreateRelationship}
        nodes={graphData?.nodes || []}
      />
    </div>
  );
}
