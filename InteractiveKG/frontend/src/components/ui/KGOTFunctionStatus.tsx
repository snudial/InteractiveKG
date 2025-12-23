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
        name: '智能问题求解功能',
        icon: Brain,
        color: 'purple',
        phases: [
          { key: 'kg_analysis', name: 'KG数据分析', description: '分析知识图谱相关数据' },
          { key: 'reasoning', name: '推理过程', description: '多轮逻辑推理分析' },
          { key: 'knowledge_update', name: '知识更新', description: '提取并更新知识图谱' },
          { key: 'complete', name: '求解完成', description: '生成最终解决方案' }
        ]
      };
    } else {
      return {
        name: '纯内部检索功能',
        icon: Database,
        color: 'blue',
        phases: [
          { key: 'kg_analysis', name: 'KG数据检索', description: '检索相关知识图谱数据' },
          { key: 'reasoning', name: '数据分析', description: '分析检索到的数据' },
          { key: 'complete', name: '检索完成', description: '生成基于内部数据的回答' }
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
          正在执行：{functionInfo.name}
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
          <span>功能边界：{currentFunction === 'solve' ? '问题求解 + 知识更新' : '纯内部检索'}</span>
          <span>状态：执行中</span>
        </div>
      </div>
    </div>
  );
};
