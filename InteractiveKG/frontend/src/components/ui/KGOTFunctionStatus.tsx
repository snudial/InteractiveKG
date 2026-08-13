import React from 'react';
import { CheckCircle, AlertCircle, Brain, Database, Layers } from 'lucide-react';

interface KGOTFunctionStatusProps {
  currentFunction: 'solve' | 'retrieve' | null;
  executionPhase: 'kg_analysis' | 'reasoning' | 'knowledge_update' | 'complete' | null;
  isLoading: boolean;
}

export const KGOTFunctionStatus: React.FC<KGOTFunctionStatusProps> = ({
  currentFunction,
  executionPhase,
  isLoading
}) => {
  if (!currentFunction || !isLoading) return null;

  const getFunctionInfo = () => {
    if (currentFunction === 'solve') {
      return {
        name: 'Intelligent problem solving',
        icon: Brain,
        color: 'purple',
        phases: [
          { key: 'kg_analysis', name: 'KG data analysis', description: 'Analyze relevant knowledge graph data' },
          { key: 'reasoning', name: 'Reasoning', description: 'Multi-round logical reasoning' },
          { key: 'knowledge_update', name: 'Knowledge update', description: 'Extract and update the knowledge graph' },
          { key: 'complete', name: 'Solution complete', description: 'Produce the final solution' }
        ]
      };
    } else {
      return {
        name: 'Internal retrieval',
        icon: Database,
        color: 'blue',
        phases: [
          { key: 'kg_analysis', name: 'KG retrieval', description: 'Retrieve relevant knowledge graph data' },
          { key: 'reasoning', name: 'Data analysis', description: 'Analyze the retrieved data' },
          { key: 'complete', name: 'Retrieval complete', description: 'Answer using internal data only' }
        ]
      };
    }
  };

  const functionInfo = getFunctionInfo();
  const IconComponent = functionInfo.icon;

  return (
    <div className="fixed top-4 right-4 z-50 bg-white rounded-lg shadow-lg border p-4 min-w-80">
      <div className="flex items-center space-x-2 mb-3">
        <IconComponent className={`h-5 w-5 text-${functionInfo.color}-600`} />
        <h3 className="font-medium text-gray-900">
          Running: {functionInfo.name}
        </h3>
      </div>

      <div className="space-y-2">
        {functionInfo.phases.map((phase, index) => {
          const isActive = phase.key === executionPhase;
          const isCompleted = functionInfo.phases.findIndex(p => p.key === executionPhase) > index;
          
          return (
            <div
              key={phase.key}
              className={`flex items-center space-x-3 p-2 rounded ${
                isActive 
                  ? `bg-${functionInfo.color}-50 border border-${functionInfo.color}-200` 
                  : isCompleted 
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-gray-50'
              }`}
            >
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : isActive ? (
                  <div className={`h-4 w-4 rounded-full bg-${functionInfo.color}-600 animate-pulse`} />
                ) : (
                  <div className="h-4 w-4 rounded-full bg-gray-300" />
                )}
              </div>
              
              <div className="flex-1">
                <div className={`text-sm font-medium ${
                  isActive 
                    ? `text-${functionInfo.color}-900` 
                    : isCompleted 
                      ? 'text-green-900'
                      : 'text-gray-600'
                }`}>
                  {phase.name}
                </div>
                <div className={`text-xs ${
                  isActive 
                    ? `text-${functionInfo.color}-700` 
                    : isCompleted 
                      ? 'text-green-700'
                      : 'text-gray-500'
                }`}>
                  {phase.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>Scope: {currentFunction === 'solve' ? 'Problem solving + knowledge update' : 'Internal retrieval only'}</span>
          <span>Status: running</span>
        </div>
      </div>
    </div>
  );
};
