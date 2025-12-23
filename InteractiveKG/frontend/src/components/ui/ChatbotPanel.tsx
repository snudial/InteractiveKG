'use client';

import React, { useState, useEffect } from 'react';
import {
  MessageCircle,
  Bot,
  Loader2,
  AlertCircle,
  Play,
  RotateCcw,
  CheckCircle,
  ArrowRight
} from 'lucide-react';

import {
  TestPhase,
  TestScenario,
  ChatbotPanelProps,
  UIInstructions,
  DataSourceSelectionButton
} from '@/types/chatbot';
import { ChatbotAPI } from '@/lib/chatbot-api';

import { useHighlight } from '@/hooks/useHighlight';
import '@/styles/scrollbar.css';

const ChatbotPanel: React.FC<ChatbotPanelProps> = ({
  onDataUpdate,
  onHighlightNodes,
  onOpenPropertyPanel,
  onTriggerKGOTSearch,
  currentGraphData
}) => {
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentPhase, setCurrentPhase] = useState<TestPhase>(TestPhase.CASE1_INTRO);
  const [currentScenario, setCurrentScenario] = useState<TestScenario | undefined>();
  const [progress, setProgress] = useState(0);
  const [uiInstructions, setUIInstructions] = useState<UIInstructions>({});
  const [error, setError] = useState<string | null>(null);
  const [advanceButton, setAdvanceButton] = useState<any>(null);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const [errorDatasetLoaded, setErrorDatasetLoaded] = useState<string | null>(null);
  const [isLoadingErrorData, setIsLoadingErrorData] = useState(false);
  const [dataSourceSelectionButtons, setDataSourceSelectionButtons] = useState<DataSourceSelectionButton[]>([]);

  
  const getPhaseGuidance = (phase: TestPhase): { title: string; description: string; panelHint?: string } | null => {
    switch (phase) {
      
      case TestPhase.CASE1_INTRO:
        return {
          title: 'Case 1 - InteractiveKG Exploration',
          description: 'Compare LLM text response with knowledge graph visualization',
          panelHint: 'Select a domain to begin exploring'
        };
      case TestPhase.CASE1_LLM_RESPONSE:
        return {
          title: 'Initial Exploration',
          description: 'The same content you previously read through text has been transformed into a knowledge graph',
          panelHint: ' Examine the distribution of nodes and relationships in the graph'
        };
      case TestPhase.CASE1_EXPLORE_GRAPH:
        return {
          title: 'Explore Knowledge Graph Visualization',
          description: 'Transform complex graphs into community views, extracting key information for better understanding',
          panelHint: ' Use the "Hierarchical Analysis" panel to navigate different levels of detail'
        };
      case TestPhase.CASE1_IDENTIFY_ERRORS:
        return {
          title: 'Identifying Unexpected Nodes / Relationships',
          description: 'When you don\'t understand why a node is in a certain position or how to interpret the information it represents, you can use the "node explaination" feature to get a better understanding.',
          panelHint: ' Double click on a node to activate the explanation feature'
        };
      case TestPhase.CASE1_EDIT_CORRECT:
        return {
          title: 'Edit and Correct',
          description: 'After identifying problem nodes/relationships, you can now edit the knowledge graph to impact LLM reasoning',
          panelHint: ' Double click on nodes or relationships and edit their properties'
        };
      case TestPhase.CASE1_REQUERY_COMPARE:
        return {
          title: 'Re-query and Compare',
          description: 'Query with the corrected knowledge graph and compare results',
          panelHint: 'Use the "Internal Retrieve" function to query with the updated graph'
        };

      
      case TestPhase.CASE2_INTRO:
        return {
          title: 'Case 2 - InteractiveKG Exploration',
          description: 'Compare LLM text response with knowledge graph visualization',
          panelHint: ' Select a domain to begin exploring'
        };
      case TestPhase.CASE2_LLM_RESPONSE:
        return {
          title: 'Initial Exploration',
          description: 'The same content you previously read through text has been transformed into a knowledge graph',
          panelHint: ' Examine the distribution of nodes and relationships in the graph'
        };
      case TestPhase.CASE2_EXPLORE_GRAPH:
        return {
          title: 'Explore Knowledge Graph Visualization',
          description: 'Transform complex graphs into community views, extracting key information for better understanding',
          panelHint: ' Use the "Hierarchical Analysis" panel to navigate different levels of detail'
        };
      case TestPhase.CASE2_IDENTIFY_ERRORS:
        return {
          title: 'Identifying Unexpected Nodes / Relationships',
          description: 'When you don\'t understand why a node is in a certain position or how to interpret the information it represents, you can use the "node explaination" feature to get a better understanding.',
          panelHint: ' Double click on a node to activate the explanation feature'
        };
      case TestPhase.CASE2_EDIT_CORRECT:
        return {
          title: 'Edit',
          description: 'After identifying problem nodes/relationships, you can now edit the knowledge graph to impact LLM reasoning',
          panelHint: ' Double click on nodes or relationships and edit their properties'
        };
      case TestPhase.CASE2_REQUERY_COMPARE:
        return {
          title: 'Re-query and Compare',
          description: 'Query with the corrected knowledge graph and compare results',
          panelHint: 'Use the "Internal Retrieve" function to query with the updated graph'
        };

      default:
        return null;
    }
  };

  
  const { highlightPhase, clearHighlight, clearAllHighlights, highlightState } = useHighlight();



  
  useEffect(() => {
    initializeSession();
  }, []);

  
  useEffect(() => {
    if (sessionId) {
      
      const timer = setTimeout(() => {
        sendWelcomeMessage(sessionId);
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [sessionId]);

  
  useEffect(() => {
    return () => {
      console.log('🎯 ChatbotPanel: Component unmounting, clearing all highlight effects');
      clearAllHighlights();
    };
  }, [clearAllHighlights]);

  const initializeSession = async () => {
    try {
      const response = await ChatbotAPI.createSession();
      if (response.success) {
        setSessionId(response.session_id);
        
        (window as any).chatbotSessionId = response.session_id;
        setCurrentPhase(TestPhase.CASE1_INTRO);
        setProgress(0);
        
      }
    } catch (error) {
      console.error('Session initialization failed:', error);
      setError('Failed to initialize chat session, please refresh the page and try again.');
    }
  };

  const sendWelcomeMessage = async (sessionId: string) => {
    try {
      const response = await ChatbotAPI.sendMessage({
        session_id: sessionId,
        message: 'Welcome to KGOT system',
        action: 'welcome'
      });

      if (response.success) {
        updateChatState(response);
      }
    } catch (error) {
      console.error('Failed to send welcome message:', error);
      
      setAdvanceButton(null);
    }
  };



  const updateChatState = (response: any) => {

    
    const newPhase = response.current_phase;
    const phaseChanged = currentPhase !== newPhase;

    setCurrentPhase(newPhase);
    setCurrentScenario(response.current_scenario);
    setUIInstructions(response.ui_instructions || {});
    setAdvanceButton(response.advance_button || null);
    setDataSourceSelectionButtons(response.data_source_selection_buttons || []);

    
    console.log('🔍 ChatbotPanel - Update state:', {
      current_phase: newPhase,
      phase_changed: phaseChanged,
      advance_button: response.advance_button,
      has_button: !!response.advance_button,
      data_source_buttons: response.data_source_selection_buttons
    });

    
    if (phaseChanged) {
      console.log(`🎯 ChatbotPanel: Phase change detected ${currentPhase} -> ${newPhase}`);

      
      
      if (newPhase === TestPhase.CASE1_REQUERY_COMPARE) {
        
        console.log(`🎯 ChatbotPanel: Case 1 re-query phase, switching KGOT panel to retrieve tab`);
        if (onTriggerKGOTSearch) {
          onTriggerKGOTSearch('', 'retrieve');
        }
      } else if (newPhase === TestPhase.CASE2_REQUERY_COMPARE) {
        
        console.log(`🎯 ChatbotPanel: Case 2 re-query phase, switching KGOT panel to retrieve tab`);
        if (onTriggerKGOTSearch) {
          onTriggerKGOTSearch('', 'retrieve');
        }
      }

      const functionalPhases = [
        
        TestPhase.CASE1_EXPLORE_GRAPH,
        TestPhase.CASE1_IDENTIFY_ERRORS,
        TestPhase.CASE1_EDIT_CORRECT,
        TestPhase.CASE1_REQUERY_COMPARE,

        
        TestPhase.CASE2_EXPLORE_GRAPH,
        TestPhase.CASE2_IDENTIFY_ERRORS,
        TestPhase.CASE2_EDIT_CORRECT,
        TestPhase.CASE2_REQUERY_COMPARE,
      ];

      if (functionalPhases.includes(newPhase)) {
        
        setTimeout(() => {
          console.log(`🎯 ChatbotPanel: Triggering highlight for phase ${newPhase} in updateChatState`);
          highlightPhase(newPhase);
        }, 800); 
      } else {
        
        console.log(`🎯 ChatbotPanel: Clearing highlights in updateChatState, phase ${newPhase} does not need highlighting`);
        setTimeout(() => {
          clearAllHighlights();
        }, 100);
      }
    }

    
    updateProgress();
  };

  const updateProgress = async () => {
    if (!sessionId) return;

    try {
      const sessionInfo = await ChatbotAPI.getSessionInfo(sessionId);
      setProgress(sessionInfo.progress_percentage * 100);
    } catch (error) {
      console.error('Failed to update progress:', error);
    }
  };

  const handleAdvancePhase = async () => {
    if (!sessionId || !advanceButton || isAdvancing) return;

    setIsAdvancing(true);
    setError(null);

    try {
      const response = await ChatbotAPI.advancePhase(sessionId, advanceButton.target_phase);

      if (response.success) {
        
        const newPhase = response.current_phase;
        setCurrentPhase(newPhase);

        
        setAdvanceButton(response.advance_button || null);
        setDataSourceSelectionButtons(response.data_source_selection_buttons || []);

        console.log(`✅ Phase advanced to: ${newPhase}`, {
          hasAdvanceButton: !!response.advance_button,
          advanceButton: response.advance_button
        });

        
        updateProgress();

        
        console.log(`🎯 ChatbotPanel: Phase switched to ${newPhase}, managing highlight display and KGOT panel state`);

        
        if (newPhase === TestPhase.CASE1_REQUERY_COMPARE) {
          
          console.log(`🎯 ChatbotPanel: Case 1 re-query phase, switching KGOT panel to retrieve tab`);
          if (onTriggerKGOTSearch) {
            onTriggerKGOTSearch('', 'retrieve');
          }
        } else if (newPhase === TestPhase.CASE2_REQUERY_COMPARE) {
          
          console.log(`🎯 ChatbotPanel: Case 2 re-query phase, switching KGOT panel to retrieve tab`);
          if (onTriggerKGOTSearch) {
            onTriggerKGOTSearch('', 'retrieve');
          }
        }

        const functionalPhases = [
          
          TestPhase.CASE1_EXPLORE_GRAPH,
          TestPhase.CASE1_IDENTIFY_ERRORS,
          TestPhase.CASE1_EDIT_CORRECT,
          TestPhase.CASE1_REQUERY_COMPARE,

          
          TestPhase.CASE2_EXPLORE_GRAPH,
          TestPhase.CASE2_IDENTIFY_ERRORS,
          TestPhase.CASE2_EDIT_CORRECT,
          TestPhase.CASE2_REQUERY_COMPARE,
        ];

        if (functionalPhases.includes(newPhase)) {
          
          setTimeout(() => {
            console.log(`🎯 ChatbotPanel: Triggering highlight for phase ${newPhase}`);
            highlightPhase(newPhase);
          }, 1000); 
        } else {
          
          console.log(`🎯 ChatbotPanel: Phase ${newPhase} does not need highlight, clearing all highlights`);
          setTimeout(() => {
            clearAllHighlights();
          }, 100);
        }

        
        setTimeout(async () => {
          try {
            const newResponse = await ChatbotAPI.sendMessage({
              session_id: sessionId,
              message: "Continue"
            });
            if (newResponse.success) {
              updateChatState(newResponse);
            }
          } catch (error) {
            console.error('Failed to get new phase guidance:', error);
          }
        }, 500);

      } else {
        setError(response.message || 'Phase advancement failed');
      }
    } catch (error) {
      console.error('Phase advancement failed:', error);
      setError('Phase advancement failed, please try again.');
    } finally {
      setIsAdvancing(false);
    }
  };



  
  const autoLoadErrorData = async () => {
    const defaultDatasetId = 'quantum_computing_errors'; 

    setIsLoadingErrorData(true);
    setError(null);

    try {
      console.log(`🔄 Automatically loading error dataset: ${defaultDatasetId}`);

      
      const response = await fetch('/api/kgot/load-error-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dataset_id: defaultDatasetId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setErrorDatasetLoaded(defaultDatasetId);

        
        if (onDataUpdate) {
          
          setTimeout(() => {
            onDataUpdate();
          }, 1000);
        }



        console.log(`✅ Error dataset loaded successfully: ${result.message}`);
      } else {
        throw new Error(result.error || 'Load failed');
      }

    } catch (error) {
      console.error('Failed to automatically load error data:', error);
      setError(`Failed to automatically load error data: ${error instanceof Error ? error.message : 'Unknown error'}`);


    } finally {
      setIsLoadingErrorData(false);
    }
  };

  const loadScenario = async (scenario: TestScenario) => {
    try {
      setIsLoading(true);
      const response = await ChatbotAPI.loadScenario({
        session_id: sessionId,
        scenario
      });
      
      if (response.success) {
        setCurrentScenario(scenario);
        
        if (onDataUpdate) {
          setTimeout(() => {
            onDataUpdate();
          }, 1000);
        }
        

      } else {
        setError(response.error || 'Failed to load scenario data');
      }
    } catch (error) {
      console.error('Failed to load scenario:', error);
      setError('Failed to load scenario data, please retry.');
    } finally {
      setIsLoading(false);
    }
  };



  
  const handleDataSourceSelection = async (domainFile: string) => {
    if (!sessionId) return;

    try {
      setIsLoading(true);
      setError(null);

      console.log(`🎯 ChatbotPanel: Loading domain data from ${domainFile}`);
      await loadSampleData(domainFile);
    } catch (error) {
      console.error('Domain selection failed:', error);
      setError('Domain selection failed, please retry.');
    } finally {
      setIsLoading(false);
    }
  };

  
  const loadSampleData = async (dataFileName: string) => {
    try {
      setIsLoading(true);

      console.log(`🎯 ChatbotPanel: Loading sample data from ${dataFileName}`);

      
      
      const dataResponse = await fetch(`http://localhost:8000/api/chatbot/sample-data/${dataFileName}`);

      if (dataResponse.ok) {
        const sampleData = await dataResponse.json();
        console.log(`🎯 ChatbotPanel: Successfully loaded sample data`, sampleData);

        
        try {
          console.log('🔄 Clearing backend database...');
          await fetch('http://localhost:8000/api/graph/data', {
            method: 'DELETE'
          });

          console.log('📤 Importing sample data to backend...');
          const importResponse = await fetch('http://localhost:8000/api/graph/import', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(sampleData)
          });

          if (importResponse.ok) {
            console.log('✅ Sample data successfully imported to backend');

            
            
            
            
            
            if (onDataUpdate) {
              onDataUpdate();
            }
          } else {
            console.warn('⚠️ Failed to import sample data to backend');
          }
        } catch (backendError) {
          console.warn('⚠️ Backend import failed:', backendError);
        }

        
        let targetPhase = '';
        if (currentPhase === TestPhase.CASE1_INTRO) {
          targetPhase = 'case1_llm_response';
        } else if (currentPhase === TestPhase.CASE2_INTRO) {
          targetPhase = 'case2_llm_response';
        }

        if (targetPhase) {
          const advanceResponse = await ChatbotAPI.advancePhase(sessionId, targetPhase);
          if (advanceResponse.success) {
            setCurrentPhase(advanceResponse.current_phase);
            updateProgress();

            
            try {
              const sessionInfo = await ChatbotAPI.getSessionInfo(sessionId);
              setAdvanceButton(sessionInfo.advance_button || null);
              setDataSourceSelectionButtons(sessionInfo.data_source_selection_buttons || []);
              console.log('🔄 Updated session info after loading sample data:', {
                phase: sessionInfo.current_phase,
                hasAdvanceButton: !!sessionInfo.advance_button,
                advanceButton: sessionInfo.advance_button
              });
            } catch (error) {
              console.error('Failed to fetch session info after loading sample data:', error);
              setAdvanceButton(null);
            }
          }
        }
      } else {
        throw new Error('Failed to load sample data file');
      }
    } catch (error) {
      console.error('Failed to load sample data:', error);
      setError(`Failed to load sample data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const resetSession = async () => {
    try {
      if (sessionId) {
        await ChatbotAPI.updateProgress(sessionId, 'reset');
      }

      
      setCurrentPhase(TestPhase.CASE1_INTRO);
      setCurrentScenario(undefined);
      setProgress(0);
      setUIInstructions({});
      setError(null);
      setAdvanceButton(null);
      setDataSourceSelectionButtons([]);

      await initializeSession();
    } catch (error) {
      console.error('Failed to reset session:', error);
      setError('Failed to reset session, please refresh the page.');
    }
  };

  const getPhaseDisplayName = (phase: TestPhase): string => {
    const phaseNames = {
      
      [TestPhase.CASE1_INTRO]: 'Case 1 - Introduction',
      [TestPhase.CASE1_LLM_RESPONSE]: 'Case 1 - LLM Response',
      [TestPhase.CASE1_EXPLORE_GRAPH]: 'Case 1 - Explore Graph',
      [TestPhase.CASE1_IDENTIFY_ERRORS]: 'Case 1 - Identify Errors',
      [TestPhase.CASE1_EDIT_CORRECT]: 'Case 1 - Edit & Correct',
      [TestPhase.CASE1_REQUERY_COMPARE]: 'Case 1 - Re-query & Compare',

      
      [TestPhase.CASE2_INTRO]: 'Case 2 - Introduction',
      [TestPhase.CASE2_LLM_RESPONSE]: 'Case 2 - LLM Response',
      [TestPhase.CASE2_EXPLORE_GRAPH]: 'Case 2 - Explore & Verify',
      [TestPhase.CASE2_IDENTIFY_ERRORS]: 'Case 2 - Identify Errors',
      [TestPhase.CASE2_EDIT_CORRECT]: 'Case 2 - Edit',
      [TestPhase.CASE2_REQUERY_COMPARE]: 'Case 2 - Re-query & Compare'
    };
    return phaseNames[phase] || phase;
  };

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      {}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5 text-purple-600" />
            <h3 className="text-lg font-medium text-gray-900">InteractiveKG Guide Assistant</h3>
          </div>
          <button
            onClick={resetSession}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
            title="Reset Session"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
        
        {}
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Current Phase: {getPhaseDisplayName(currentPhase)}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-purple-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {}
      {getPhaseGuidance(currentPhase) && (
        <div className="flex-shrink-0 bg-purple-50 border-t border-gray-200/50 border-l-4 border-l-purple-400">
          <div className="px-4 py-3 space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
              <div className="text-sm font-semibold text-purple-900">
                Current Phase Guidance
              </div>
            </div>
            <div className="text-sm font-medium text-gray-900 pl-4">
              {getPhaseGuidance(currentPhase)?.title}
            </div>
            <div className="text-xs text-gray-700 leading-relaxed pl-4 bg-white/50 p-2 rounded">
              💡 {getPhaseGuidance(currentPhase)?.description}
            </div>
            {getPhaseGuidance(currentPhase)?.panelHint && (
              <div className="text-xs text-purple-700 leading-relaxed pl-4 bg-purple-100/50 p-2 rounded border border-purple-200">
                🎯 <strong>Operation Tip:</strong>{getPhaseGuidance(currentPhase)?.panelHint}
              </div>
            )}
          </div>
        </div>
      )}



      {}
      {(currentPhase === TestPhase.CASE1_INTRO || currentPhase === TestPhase.CASE2_INTRO) && dataSourceSelectionButtons.length > 0 && (
        <div className="flex-1 flex flex-col bg-purple-50 border-l-4 border-l-purple-400 overflow-hidden">
          <div className="px-4 pt-6 pb-2">
            <div className="text-xs text-gray-600 text-center">
              Please select your data source:
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-4 pb-4 chatbot-track-scrollbar smooth-scroll">
            <div className="space-y-4 py-2">
              {dataSourceSelectionButtons.map((button) => (
                <button
                  key={button.id}
                  onClick={() => handleDataSourceSelection(button.file)}
                  disabled={isLoading}
                  className={`w-full px-6 py-4 rounded-lg font-medium text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg ${
                    button.variant === 'primary' ? 'bg-purple-500/80 hover:bg-purple-600 active:bg-purple-700 text-white' :
                    button.variant === 'secondary' ? 'bg-pink-500/80 hover:bg-pink-600 active:bg-pink-700 text-white' :
                    'bg-pink-600 hover:bg-pink-700 text-white'
                  }`}
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Loading...
                    </div>
                  ) : (
                    <div className="text-left">
                      <div className="font-semibold flex items-center">
                        <span className="mr-2">{button.label}</span>
                      </div>
                      <div className="text-xs opacity-90 mt-1">{button.description}</div>
                    </div>
                  )}
                </button>
              ))}
            </div>

            {"text-xs text-gray-500 mt-4 text-center bg-white/30 py-2 px-4 rounded-md"}
          </div>
        </div>
      )}

      {}
      {(() => {
        const shouldShow = advanceButton !== null;
        console.log('🔘 Advance button render check:', {
          currentPhase,
          hasAdvanceButton: !!advanceButton,
          advanceButton: advanceButton,
          shouldShow
        });
        return shouldShow;
      })() && (
        <div className="flex-shrink-0 px-4 py-2 border-t border-gray-100 bg-gray-50 mt-auto">
          <div className="text-xs text-gray-600 mb-1.5">Ready to enter next phase:</div>
          <button
            onClick={handleAdvancePhase}
            disabled={isAdvancing}
            className={`w-full px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center ${
              advanceButton.variant === 'primary'
                ? 'bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white'
                : advanceButton.variant === 'success'
                ? 'bg-purple-500 hover:bg-purple-600 active:bg-purple-700 text-white'
                : advanceButton.variant === 'warning'
                ? 'bg-purple-400 hover:bg-purple-500 active:bg-purple-600 text-white'
                : 'bg-gray-600 hover:bg-gray-700 text-white'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isAdvancing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Advancing...
              </>
            ) : (
              <>
                <ArrowRight className="h-4 w-4 mr-2" />
                {advanceButton.label}
              </>
            )}
          </button>
          <div className="text-xs text-gray-500 mt-1.5 text-center leading-tight">
            {advanceButton.description}
          </div>
        </div>
      )}



      {}
      {false && (
        <div className="border-t border-gray-100 bg-orange-50 border-l-4 border-l-orange-400">
          <div className="px-4 py-3">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-orange-900">
                  🔄 Automatically loading error dataset...
                </div>
                <div className="text-xs text-orange-700 mt-1">
                  System is loading quantum computing dataset containing AI hallucinations for subsequent anomaly detection and correction testing.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {}
      {error && (
        <div className="px-4 py-2 border-t border-red-200 bg-red-50">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}



      {}
      {highlightState.isHighlighted && (
        <div className="fixed top-4 right-4 bg-purple-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 flex items-center space-x-2">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          <span className="text-sm font-medium">
            Guiding you to use relevant features
          </span>
        </div>
      )}
    </div>
  );
};

export default ChatbotPanel;
