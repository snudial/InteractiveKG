import React, { useState } from 'react';
import { Brain, Search, MessageCircle, Loader2, AlertCircle, Database, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { kgotApi } from '@/lib/api';

interface KGOTResult {
  answer: string;
  execution_time: number;
  success: boolean;
  error?: string;
}

interface EnhancedSolveResult extends KGOTResult {
  iterations: number;
  kg_updates: number;
  reasoning_steps?: string[];
  should_refresh_graph?: boolean; 
}

interface PureRetrieveResult extends KGOTResult {
  context_nodes: number;
  retrieved_context?: string;
}

interface EnhancedKGOTPanelProps {
  onDataUpdate?: () => void; 
  useHierarchicalView?: boolean; 
  hierarchicalAbstractionLevel?: number; 
  hierarchicalViewMode?: 'unified' | 'semantic' | 'community' | 'structural'; 
  activeTab?: 'solve' | 'retrieve'; 
  suggestedQuery?: string; 
  onTabChange?: (tab: 'solve' | 'retrieve') => void; 
  defaultTab?: 'solve' | 'retrieve'; 
  showTabSwitcher?: boolean; 
  modalMode?: boolean; 
  panelViewMode?: 'community' | 'detailed'; 
}



const EnhancedKGOTPanel: React.FC<EnhancedKGOTPanelProps> = ({
  onDataUpdate,
  useHierarchicalView = false,
  hierarchicalAbstractionLevel = 3,
  hierarchicalViewMode = 'unified',
  activeTab: externalActiveTab,
  suggestedQuery = '',
  onTabChange,
  defaultTab = 'solve',
  showTabSwitcher = true,
  modalMode = false,
  panelViewMode = 'detailed'
}) => {
  const [activeTab, setActiveTab] = useState<'solve' | 'retrieve'>(defaultTab);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  
  const [problemText, setProblemText] = useState('');
  const [queryText, setQueryText] = useState('');
  const [learnFromSolution, setLearnFromSolution] = useState(true);

  
  React.useEffect(() => {
    if (externalActiveTab) {
      setActiveTab(externalActiveTab);
    }
  }, [externalActiveTab]); 

  React.useEffect(() => {
    if (suggestedQuery) {
      if (activeTab === 'solve') {
        setProblemText(suggestedQuery);
      } else {
        setQueryText(suggestedQuery);
      }
    }
  }, [suggestedQuery, activeTab]);

  
  const handleTabChange = (newTab: 'solve' | 'retrieve') => {
    setActiveTab(newTab);
    
    if (onTabChange) {
      onTabChange(newTab);
    }
  };

  const handleEnhancedSolve = async () => {
    if (!problemText.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await kgotApi.enhancedSolve<EnhancedSolveResult>({
        problem: problemText,
        learn_from_solution: learnFromSolution,
        use_hierarchical_view: useHierarchicalView,
        abstraction_level: hierarchicalAbstractionLevel,
        abstraction_mode: hierarchicalViewMode
      });
      setResult(data);

      
      if (data.success && (data.should_refresh_graph || data.kg_updates > 0) && onDataUpdate) {
        setTimeout(() => {
          onDataUpdate();
        }, 1000); 
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      const errorResult = {
        success: false,
        answer: '',
        execution_time: 0,
        iterations: 0,
        kg_updates: 0,
        error: err instanceof Error ? err.message : 'Unknown error',
        reasoning_steps: []
      };
      setResult(errorResult);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePureInternalRetrieve = async () => {
    if (!queryText.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await kgotApi.pureInternalRetrieve<PureRetrieveResult>({
        query: queryText,
        abstraction_level: hierarchicalAbstractionLevel,
        abstraction_mode: hierarchicalViewMode,
        view_mode: panelViewMode
      });
      setResult(data);
      
      if (!data.success && data.error) {
        setError(data.error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };





  return (
    <div className={`${modalMode ? '' : ''}`}>
      {showTabSwitcher && (
        <div className="flex space-x-1 mb-4">
          <button
            onClick={() => handleTabChange('solve')}
            className={`px-3 py-2 text-sm font-medium rounded-md ${
              activeTab === 'solve'
                ? 'bg-blue-50 text-blue-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <MessageCircle className="h-4 w-4 inline mr-1" />
            Intelligent Solving
          </button>
          <button
            onClick={() => handleTabChange('retrieve')}
            className={`px-3 py-2 text-sm font-medium rounded-md ${
              activeTab === 'retrieve'
                ? 'bg-blue-50 text-blue-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Search className="h-4 w-4 inline mr-1" />
            Internal Retrieval
          </button>
        </div>
      )}

      {activeTab === 'solve' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Problem Description
            </label>
            <textarea
              value={problemText}
              onChange={(e) => setProblemText(e.target.value)}
              placeholder="Enter a problem. The system will visualize the reasoning process in the graph."
              className="w-full p-3 border border-gray-300 rounded-md placeholder-gray-400 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
            />
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="learnFromSolution"
              checked={learnFromSolution}
              onChange={(e) => setLearnFromSolution(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="learnFromSolution" className="text-sm text-gray-700">
              Learn from solution and update knowledge graph
            </label>
          </div>

          <button
            onClick={handleEnhancedSolve}
            disabled={isLoading || !problemText.trim()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Brain className="h-4 w-4 mr-2" />
            )}
            {isLoading ? 'Solving...' : 'Start Intelligent Solving'}
          </button>
        </div>
      )}

      {activeTab === 'retrieve' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Query Content
            </label>
            <textarea
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Enter your query. The system will answer based solely on data in the current knowledge graph."
              className="w-full p-3 border border-gray-300 rounded-md placeholder-gray-400 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
            />
          </div>

          <button
            onClick={handlePureInternalRetrieve}
            disabled={isLoading || !queryText.trim()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Database className="h-4 w-4 mr-2" />
            )}
            {isLoading ? 'Retrieving...' : 'Start Internal Retrieval'}
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <AlertCircle className="h-4 w-4 text-red-600 mr-2" />
            <span className="text-sm text-red-600">{error}</span>
          </div>
        </div>
      )}



      {result && (
        <div className="mt-6 space-y-4 max-h-64 always-show-scrollbar" style={{minHeight: '200px'}}>
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-lg font-medium text-gray-900 mb-3">
              {activeTab === 'solve' ? 'Intelligent Solving Results' : '🔍 Knowledge Extraction Results'}
            </h3>

            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Input Question</h4>
              <div className="bg-gray-50 p-3 rounded-md border text-sm">
                <p className="text-gray-800">
                  {activeTab === 'solve' ? problemText : queryText}
                </p>
              </div>
            </div>

            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                {result.success ? 'Analysis Results' : 'Information'}
              </h4>
              <div className={`p-3 rounded-md border h-48 always-show-scrollbar ${
                result.success
                  ? 'bg-yellow-50 border-yellow-200'
                  : 'bg-orange-50 border-orange-200'
              }`} style={{minHeight: '192px'}}>
                <div className={`text-sm prose prose-sm max-w-none ${
                  result.success
                    ? 'prose-headings:text-yellow-900 prose-strong:text-yellow-900 prose-p:text-yellow-800 prose-li:text-yellow-800'
                    : 'prose-headings:text-orange-900 prose-strong:text-orange-900 prose-p:text-orange-800 prose-li:text-orange-800'
                }`}>
                  <ReactMarkdown>{result.error || result.answer || 'No information available'}</ReactMarkdown>
                </div>
              </div>
            </div>

            {result.success && (
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="inline-flex items-center px-2 py-1 rounded-full bg-yellow-100 text-yellow-800">
                  <Clock className="h-3 w-3 mr-1" />
                  {result.execution_time?.toFixed(2)}s
                </span>
                {result.iterations && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-amber-100 text-amber-800">
                    <Brain className="h-3 w-3 mr-1" />
                    {result.iterations} Reasoning Rounds
                  </span>
                )}
                {result.kg_updates !== undefined && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-yellow-100 text-yellow-800">
                    <Database className="h-3 w-3 mr-1" />
                    {result.kg_updates} Knowledge Updates
                  </span>
                )}
                {result.context_nodes && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-orange-100 text-orange-800">
                    <Search className="h-3 w-3 mr-1" />
                    {result.context_nodes} Related Nodes
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedKGOTPanel;
