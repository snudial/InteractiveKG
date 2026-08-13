'use client';

import React, { useState, useEffect } from 'react';
import { graphApi } from '@/lib/api';

interface HierarchicalAnalysis {
  abstraction_method: string;
  abstraction_levels: number;
  hierarchy: {
    level_0?: {
      label_groups?: Record<string, string[]>;
    };
  };
  color_mapping: Record<string, string>;
  community_view?: {
    nodes: Array<{
      id: string;
      name: string;
      description: string;
      node_count: number;
      member_node_ids: string[];
      type: string;
    }>;
    edges: Array<{
      source: string;
      target: string;
      weight: number;
      edge_count: number;
      edge_details?: Array<{
        source: string;
        target: string;
        type: string;
        weight: number;
      }>;
    }>;
  };
  detailed_view?: {
    nodes: Array<{
      id: string;
      label: string;
      labels: string[];
      properties: Record<string, any>;
      community_id?: string;
      community_name?: string;
    }>;
    edges: Array<{
      source: string;
      target: string;
      type: string;
      properties: Record<string, any>;
    }>;
  };
  analysis_metadata?: {
    total_nodes: number;
    total_relationships: number;
    cognitive_level: string;
    abstraction_strategy: string;
    theoretical_basis: string;
    group_count: number;
    confidence: number;
    source: string;
    view_mode?: string;
  };
}

interface HierarchicalAbstractionPanelProps {
  onAnalysisChange: (analysis: HierarchicalAnalysis | null) => void;
  onAbstractionLevelChange?: (level: number) => void;
  onFullViewChange?: (showFullView: boolean) => void;
  onViewModeChange?: (mode: 'community' | 'detailed') => void; 
  onLoadingChange?: (isLoading: boolean) => void; 
  isLoading?: boolean;
  modalMode?: boolean;
  detectionMode?: boolean; 
  refreshTrigger?: number; 
}



export const HierarchicalAbstractionPanel: React.FC<HierarchicalAbstractionPanelProps> = ({
  onAnalysisChange,
  onAbstractionLevelChange,
  onFullViewChange,
  onViewModeChange,
  onLoadingChange,
  isLoading = false,
  modalMode = false,
  detectionMode = false,
  refreshTrigger = 0
}) => {
  const [abstractionLevel, setAbstractionLevel] = useState(1); 
  const [showFullView, setShowFullView] = useState(false);
  const [viewMode, setViewMode] = useState<'community' | 'detailed'>('detailed'); 
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentAnalysis, setCurrentAnalysis] = useState<HierarchicalAnalysis | null>(null);
  const [pendingAnalysis, setPendingAnalysis] = useState<HierarchicalAnalysis | null>(null);

  const performHierarchicalAnalysis = async () => {
    setIsAnalyzing(true);
    setError(null);
    
    setPendingAnalysis(null);

    
    if (onLoadingChange) {
      onLoadingChange(true);
    }

    try {
      
      
      
      
      
      const backendLevel = abstractionLevel;

      
      const params = new URLSearchParams({
        abstraction_level: backendLevel.toString(),
        mode: 'unified', 
        use_llm: 'true' 
      });

      const analysisData = await graphApi.hierarchicalAnalysis<HierarchicalAnalysis>(params);

      
      setPendingAnalysis(analysisData);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setCurrentAnalysis(null);
      onAnalysisChange(null);
      setIsAnalyzing(false);
      
      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  };

  
  useEffect(() => {
    if (pendingAnalysis) {
      
      const timer = setTimeout(() => {
        setCurrentAnalysis(pendingAnalysis);
        onAnalysisChange(pendingAnalysis);
        setIsAnalyzing(false);
        setPendingAnalysis(null);
        
        if (onLoadingChange) {
          onLoadingChange(false);
        }
      }, 100); 

      return () => clearTimeout(timer);
    }
  }, [pendingAnalysis, onAnalysisChange, onLoadingChange]);

  
  useEffect(() => {
    performHierarchicalAnalysis();
  }, []); 

  
  useEffect(() => {
    if (!isLoading) {
      performHierarchicalAnalysis();
    }
  }, [abstractionLevel, isLoading]);

  
  useEffect(() => {
    if (onAbstractionLevelChange) {
      
      const backendLevel = abstractionLevel;
      onAbstractionLevelChange(backendLevel);
    }
  }, [abstractionLevel, onAbstractionLevelChange]);

  
  useEffect(() => {
    if (onFullViewChange) {
      onFullViewChange(showFullView);
    }
  }, [showFullView, onFullViewChange]);

  
  useEffect(() => {
    if (onViewModeChange) {
      onViewModeChange(viewMode);
    }
  }, [viewMode, onViewModeChange]);

  
  useEffect(() => {
    if (refreshTrigger > 0) {
      performHierarchicalAnalysis();
    }
  }, [refreshTrigger]);

  return (
    <div
      id="hierarchical-abstraction-panel"
      className="space-y-4"
    >
      {}
      {abstractionLevel > 0 && currentAnalysis?.community_view && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">View Mode</label>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('community')}
              disabled={isAnalyzing || isLoading}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'community'
                  ? 'bg-orange-200/80 text-orange-800'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              Community View
            </button>
            <button
              onClick={() => setViewMode('detailed')}
              disabled={isAnalyzing || isLoading}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'detailed'
                  ? 'bg-orange-200/80 text-orange-800'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              Detailed View
            </button>
          </div>
        </div>
      )}

      {}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Abstraction Level
          </label>
          <span className="text-sm text-gray-500">
            Level {abstractionLevel}
          </span>
        </div>

        <input
          type="range"
          min="0"
          max="3"
          value={abstractionLevel}
          onChange={(e) => setAbstractionLevel(parseInt(e.target.value))}
          disabled={isAnalyzing || isLoading}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />

        <div className="flex justify-between text-xs text-gray-500">
          <span>0</span>
          <span>1</span>
          <span>2</span>
          <span>3</span>
        </div>
      </div>

      {}
      {isAnalyzing && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
            <span className="text-yellow-700 text-sm font-medium">Analyzing Graph Structure...</span>
          </div>
        </div>
      )}

      {}
      {error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-blue-700 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
};

export default HierarchicalAbstractionPanel;
