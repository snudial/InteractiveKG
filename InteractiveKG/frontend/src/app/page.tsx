'use client';

import React, { useState, useEffect } from 'react';
import { FileUploadButton } from '@/components/upload/FileUploadButton';
import { GraphVisualization } from '@/components/graph/GraphVisualization';
import { PropertyPanel } from '@/components/ui/PropertyPanel';
import { CreateNodeModal } from '@/components/ui/CreateNodeModal';
import { CreateRelationshipModal } from '@/components/ui/CreateRelationshipModal';
import { HierarchicalAbstractionPanel } from '@/components/ui/HierarchicalAbstractionPanel';
import EnhancedKGOTPanel from '@/components/ui/EnhancedKGOTPanel';
import ChatbotPanel from '@/components/ui/ChatbotPanel';
import { GraphAPI } from '@/lib/api';
import { GraphData, NodeData, RelationshipData, NodeCreateRequest } from '@/types/graph';
import { Download, RefreshCw, Trash2, Database, Plus, Link, Upload, Settings, BarChart3, MessageSquare } from 'lucide-react';

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
  const [isHierarchicalAnalyzing, setIsHierarchicalAnalyzing] = useState(false); 
  const [useHierarchicalView, setUseHierarchicalView] = useState(false);
  const [hierarchicalViewMode] = useState<'unified'>('unified');
  const [hierarchicalAbstractionLevel, setHierarchicalAbstractionLevel] = useState(1);
  const [showFullView, setShowFullView] = useState(false);
  const [hierarchicalRefreshTrigger, setHierarchicalRefreshTrigger] = useState(0); 
  const [visibleNodeIds, setVisibleNodeIds] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'community' | 'detailed'>('detailed'); 

  
  const [highlightedNodes, setHighlightedNodes] = useState<string[]>([]);
  const [activeKGOTTab, setActiveKGOTTab] = useState<'solve' | 'retrieve'>('solve');

  
  
  const calculateVisibleNodes = (): number => {
    
    if (hierarchicalAbstractionLevel === 0) {
      return graphData.nodes.filter(node => !node.labels?.includes('Community')).length;
    }
    
    return graphData.nodes.filter(node => !node.labels?.includes('Community')).length;
  };

  
  useEffect(() => {
    
    const hasAnalysis = !!hierarchicalAnalysis;

    if (hasAnalysis && !useHierarchicalView) {
      setUseHierarchicalView(true);
    }
  }, [!!hierarchicalAnalysis, useHierarchicalView]); 

  
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

  const loadGraphData = async (sampleData?: any) => {
    setIsLoading(true);
    setError(null);

    try {
      
      if (sampleData) {

        
        const loadResponse = await GraphAPI.loadSampleData(sampleData);
        if (loadResponse.error) {
          console.error('Failed to load sample data to database:', loadResponse.error);
          setError(loadResponse.error);
          return;
        }


        
        const response = await GraphAPI.getAllGraphData();
        if (response.error) {
          setError(response.error);
          return;
        }

        
        if (response.data) {
          setGraphData(response.data);

          
          await loadGroupingAnalysis();

        } else {
          setError('No data received from server after sample data loading');
        }
        return;
      }

      
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
    
  };

  const handleNodeDoubleClick = (node: NodeData) => {
    setSelectedNode(node);
    setSelectedRelationship(null);
    setIsPanelOpen(true);
  };

  const handleRelationshipSelect = (relationship: RelationshipData | null) => {
    setSelectedRelationship(relationship);
    setSelectedNode(null);
    setIsPanelOpen(!!relationship);
  };

  const handleRelationshipDoubleClick = (relationship: RelationshipData) => {
    setSelectedRelationship(relationship);
    setSelectedNode(null);
    setIsPanelOpen(true);
  };

  const handleInsertNode = async () => {
    
    await loadGraphData();
    setSelectedRelationship(null);
    setIsPanelOpen(false);
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
          
          setHierarchicalRefreshTrigger(prev => prev + 1);
          setIsPanelOpen(false);
        }
      } else if (selectedRelationship) {
        setIsPanelOpen(false);
      }
    } catch (err) {
      setError('Failed to save changes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete the selected item? This action cannot be undone.')) {
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
          
          setHierarchicalRefreshTrigger(prev => prev + 1);
          setSelectedNode(null);
          setIsPanelOpen(false);
        }
      } else if (selectedRelationship) {
        const response = await GraphAPI.deleteRelationship(selectedRelationship.id);
        if (response.error) {
          setError(response.error);
        } else {
          await loadGraphData();
          
          setHierarchicalRefreshTrigger(prev => prev + 1);
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
    if (confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
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
  };

  const handleKGOTTabChange = (tab: 'solve' | 'retrieve') => {
    setActiveKGOTTab(tab);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-slate-200">
      {}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-full mx-auto px-4 lg:px-8">
          <div className="flex flex-wrap justify-between items-center gap-y-2 min-h-16 py-2">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Database className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">InteractiveKG</h1>
                  <p className="text-sm text-gray-500 hidden md:block">User-Controllable Knowledge Graph Reasoning</p>
                </div>
              </div>

              {}
              <div className="hidden lg:flex items-center space-x-4 ml-8">
                <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-full">
                  <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-green-700">{graphData.nodes.length} Nodes</span>
                </div>
                <div className="flex items-center space-x-2 px-3 py-1.5 bg-orange-50 border border-orange-200 rounded-full">
                  <div className="h-2 w-2 bg-orange-500 rounded-full"></div>
                  <span className="text-sm font-medium text-orange-700">{graphData.relationships.length} Relations</span>
                </div>
              </div>
            </div>

            {}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center space-x-2 bg-gray-50 rounded-xl p-1">
                <FileUploadButton
                  onUploadSuccess={handleUploadSuccess}
                  onUploadError={handleUploadError}
                />

                <button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-all duration-200 hover:shadow-md"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Node
                </button>

                <button
                  onClick={() => setIsCreateRelModalOpen(true)}
                  disabled={!graphData || graphData.nodes.length < 2}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-all duration-200 hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Link className="h-4 w-4 mr-2" />
                  Create Relation
                </button>
              </div>

              <div className="h-8 w-px bg-gray-300"></div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={loadGraphData}
                  disabled={isLoading}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 hover:shadow-md disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>

                <button
                  onClick={handleExport}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 hover:shadow-md"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </button>

                <button
                  onClick={handleClearAll}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-all duration-200 hover:shadow-md"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {}
      {error && (
        <div className="max-w-full mx-auto px-6 lg:px-8 pt-4">
          <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-r-lg shadow-sm">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-700 font-medium">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {}
      <main className="max-w-full mx-auto px-4 lg:px-8 py-6">
        <div className="flex flex-col lg:flex-row gap-6 lg:h-[calc(100vh-180px)]">
          {}
          <div className="w-full lg:w-72 xl:w-80 flex flex-col space-y-6 lg:h-full">
            {}
            <div id="hierarchical-abstraction-panel" className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden flex-shrink-0">
              <div className="px-5 py-4 border-b border-gray-200/50 bg-gradient-to-r from-orange-50 to-red-50">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-gradient-to-r from-orange-400 to-red-500 rounded-lg flex items-center justify-center">
                    <BarChart3 className="h-4 w-4 text-white" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">Hierarchical Analysis</h3>
                </div>
              </div>
              <div className="p-5">
                <HierarchicalAbstractionPanel
                  onAnalysisChange={setHierarchicalAnalysis}
                  onAbstractionLevelChange={setHierarchicalAbstractionLevel}
                  onFullViewChange={setShowFullView}
                  onViewModeChange={setViewMode}
                  onLoadingChange={setIsHierarchicalAnalyzing}
                  isLoading={isLoading}
                  refreshTrigger={hierarchicalRefreshTrigger}
                />
              </div>
            </div>

            {}
            <div
              id={activeKGOTTab === 'solve' ? 'enhanced-kgot-panel-solve' : 'enhanced-kgot-panel-retrieve'}
              className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden lg:flex-1 lg:flex lg:flex-col lg:min-h-0"
            >
              <div className="px-5 py-4 border-b border-gray-200/50 bg-yellow-50">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                    <Settings className="h-4 w-4 text-white" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">Knowledge Reasoning</h3>
                </div>
              </div>
              <div className="p-5 lg:flex-1 lg:min-h-0 lg:overflow-y-auto custom-scrollbar">
                <EnhancedKGOTPanel
                  onDataUpdate={loadGraphData}
                  useHierarchicalView={useHierarchicalView}
                  hierarchicalAbstractionLevel={hierarchicalAbstractionLevel}
                  hierarchicalViewMode={hierarchicalViewMode}
                  activeTab={activeKGOTTab}
                  onTabChange={handleKGOTTabChange}
                  panelViewMode={viewMode}
                />
              </div>
            </div>
          </div>

          {}
          <div className="flex-1 min-w-0">
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 h-[60vh] lg:h-full overflow-hidden flex flex-col">
              <div className="px-5 py-4 border-b border-gray-200/50 bg-gradient-to-r from-slate-50 to-gray-50">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">Knowledge Graph Visualization of LLM Responses</h2>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Visible Nodes: {showFullView ? graphData.nodes.length : calculateVisibleNodes()}</span>
                    <span className="text-gray-400">|</span>
                    <span>Abstraction Level: {showFullView ? 1 : hierarchicalAbstractionLevel}</span>
                  </div>
                </div>
              </div>
              
              <div className="relative flex-1 min-h-0">
                <GraphVisualization
                  data={graphData}
                  groupingAnalysis={groupingAnalysis}
                  hierarchicalAnalysis={hierarchicalAnalysis}
                  viewMode={hierarchicalViewMode}
                  useHierarchicalView={useHierarchicalView}
                  abstractionLevel={showFullView ? 1 : hierarchicalAbstractionLevel}
                  panelViewMode={viewMode}
                  onNodeSelect={handleNodeSelect}
                  onNodeDoubleClick={handleNodeDoubleClick}
                  onRelationshipSelect={handleRelationshipSelect}
                  onRelationshipDoubleClick={handleRelationshipDoubleClick}
                  onVisibleNodesChange={setVisibleNodeIds}
                  highlightedNodes={highlightedNodes}
                />

                {}
                {isHierarchicalAnalyzing && (
                  <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-30">
                    <div className="bg-white rounded-lg shadow-xl p-6 flex flex-col items-center space-y-4">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600"></div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-gray-900">Analyzing Graph Structure</div>
                        <div className="text-sm text-gray-600 mt-1">Please wait while we process the data...</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {}
          <div className="w-full lg:w-72 xl:w-80">
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 h-[70vh] lg:h-full overflow-hidden flex flex-col">
              <div className="px-5 py-4 border-b border-gray-200/50 bg-purple-50">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-purple-500 rounded-lg flex items-center justify-center">
                    <MessageSquare className="h-4 w-4 text-white" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">Guide Assistant</h3>
                </div>
              </div>
              <div className="flex-1 min-h-0">
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
        onInsertNode={handleInsertNode}
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