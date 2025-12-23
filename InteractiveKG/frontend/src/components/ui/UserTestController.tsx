'use client';

import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle,
  ArrowRight,
  Eye,
  Edit,
  Search,
  Trash2
} from 'lucide-react';

import { 
  TestScenario, 
  TestPhase, 
  SessionInfo 
} from '@/types/chatbot';
import { ChatbotAPI } from '@/lib/chatbot-api';

interface UserTestControllerProps {
  sessionId: string;
  onPhaseChange?: (phase: TestPhase) => void;
  onScenarioLoad?: (scenario: TestScenario) => void;
  onDataUpdate?: () => void;
}

const UserTestController: React.FC<UserTestControllerProps> = ({
  sessionId,
  onPhaseChange,
  onScenarioLoad,
  onDataUpdate
}) => {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionId) {
      loadSessionInfo();
    }
  }, [sessionId]);

  const loadSessionInfo = async () => {
    try {
      const info = await ChatbotAPI.getSessionInfo(sessionId);
      setSessionInfo(info);
      if (onPhaseChange) {
        onPhaseChange(info.current_phase);
      }
    } catch (error) {
      console.error('Failed to load session info:', error);
      setError('Failed to load session info');
    }
  };

  const loadScenario = async (scenario: TestScenario) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await ChatbotAPI.loadScenario({
        session_id: sessionId,
        scenario
      });

      if (response.success) {
        await loadSessionInfo();
        if (onScenarioLoad) {
          onScenarioLoad(scenario);
        }
        if (onDataUpdate) {
          setTimeout(() => {
            onDataUpdate();
          }, 1000);
        }
      } else {
        setError(response.error || '加载场景失败');
      }
    } catch (error) {
      console.error('加载场景失败:', error);
      setError('加载场景失败');
    } finally {
      setIsLoading(false);
    }
  };

  const advancePhase = async (targetPhase?: TestPhase) => {
    try {
      setIsLoading(true);
      await ChatbotAPI.updateProgress(sessionId, 'next_phase', targetPhase);
      await loadSessionInfo();
    } catch (error) {
      console.error('推进阶段失败:', error);
      setError('推进阶段失败');
    } finally {
      setIsLoading(false);
    }
  };

  const resetTest = async () => {
    try {
      setIsLoading(true);
      await ChatbotAPI.updateProgress(sessionId, 'reset');
      await loadSessionInfo();
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      console.error('重置测试失败:', error);
      setError('重置测试失败');
    } finally {
      setIsLoading(false);
    }
  };

  const completeAct = async () => {
    try {
      setIsLoading(true);
      await ChatbotAPI.updateProgress(sessionId, 'complete_act');
      await loadSessionInfo();
    } catch (error) {
      console.error('完成Act失败:', error);
      setError('完成Act失败');
    } finally {
      setIsLoading(false);
    }
  };

  const getPhaseInstructions = (phase: TestPhase): string => {
    const instructions = {
      [TestPhase.WELCOME]: '欢迎使用交互式知识图谱研究系统！',
      [TestPhase.ROLE_SETUP]: '您将扮演资深金融风险分析师角色',
      [TestPhase.ACT_I_INTRO]: '准备开始Act I: 静态KG挑战',
      [TestPhase.ACT_I_QUERY]: '使用"纯内部检索"功能提出问题',
      [TestPhase.ACT_I_ANALYSIS]: '分析查询结果，发现过时数据问题',
      [TestPhase.ACT_I_CORRECTION]: '使用属性编辑器修正过时数据',
      [TestPhase.ACT_II_INTRO]: '准备开始Act II: 动态KG挑战',
      [TestPhase.ACT_II_REASONING]: '使用"为什么？"功能理解AI推理',
      [TestPhase.ACT_II_CLEANUP]: '识别并清理AI幻觉节点和关系',
      [TestPhase.ACT_II_FINAL]: '基于清理后的KG生成最终报告',
      [TestPhase.COMPLETED]: '恭喜完成所有测试！'
    };
    return instructions[phase] || '继续测试流程';
  };

  const getPhaseActions = (phase: TestPhase) => {
    switch (phase) {
      case TestPhase.ACT_I_INTRO:
        return (
          <button
            onClick={() => loadScenario(TestScenario.ACT_I)}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <Play className="h-4 w-4 mr-2" />
            Load Act I Data
          </button>
        );
      
      case TestPhase.ACT_I_QUERY:
        return (
          <div className="flex items-center space-x-2 text-sm text-blue-600">
            <Search className="h-4 w-4" />
            <span>Please use the "Pure Internal Retrieval" function on the left</span>
          </div>
        );
      
      case TestPhase.ACT_I_ANALYSIS:
        return (
          <div className="flex items-center space-x-2 text-sm text-orange-600">
            <Eye className="h-4 w-4" />
            <span>Observe graph visualization, look for problematic data</span>
          </div>
        );
      
      case TestPhase.ACT_I_CORRECTION:
        return (
          <div className="flex items-center space-x-2 text-sm text-green-600">
            <Edit className="h-4 w-4" />
            <span>Use property editor to correct data</span>
          </div>
        );
      
      case TestPhase.ACT_II_INTRO:
        return (
          <button
            onClick={() => loadScenario(TestScenario.ACT_II)}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            <Play className="h-4 w-4 mr-2" />
            Load Act II Data
          </button>
        );
      
      case TestPhase.ACT_II_CLEANUP:
        return (
          <div className="flex items-center space-x-2 text-sm text-red-600">
            <Trash2 className="h-4 w-4" />
            <span>Identify and delete hallucination nodes and relationships</span>
          </div>
        );
      
      default:
        return null;
    }
  };

  if (!sessionInfo) {
    return (
      <div className="p-4 text-center text-gray-500">
        加载测试控制器...
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">测试流程控制</h3>
        <button
          onClick={resetTest}
          disabled={isLoading}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
          title="重置测试"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      {}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
          <span>测试进度</span>
          <span>{Math.round(sessionInfo.progress_percentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${sessionInfo.progress_percentage}%` }}
          />
        </div>
      </div>

      {}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
          <span className="font-medium text-gray-900">
            {sessionInfo.phase_description}
          </span>
        </div>
        <p className="text-sm text-gray-600 ml-5">
          {getPhaseInstructions(sessionInfo.current_phase)}
        </p>
      </div>

      {}
      <div className="mb-4">
        {getPhaseActions(sessionInfo.current_phase)}
      </div>

      {}
      <div className="flex items-center space-x-4 text-sm">
        <div className="flex items-center space-x-1">
          {sessionInfo.act_1_completed ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <div className="w-4 h-4 border-2 border-gray-300 rounded-full"></div>
          )}
          <span className={sessionInfo.act_1_completed ? 'text-green-600' : 'text-gray-500'}>
            Act I
          </span>
        </div>
        
        <div className="flex items-center space-x-1">
          {sessionInfo.act_2_completed ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <div className="w-4 h-4 border-2 border-gray-300 rounded-full"></div>
          )}
          <span className={sessionInfo.act_2_completed ? 'text-green-600' : 'text-gray-500'}>
            Act II
          </span>
        </div>
      </div>

      {}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-4 p-2 bg-gray-100 rounded text-xs text-gray-600">
          <div>Phase: {sessionInfo.current_phase}</div>
          <div>Scenario: {sessionInfo.current_scenario || 'None'}</div>
          <div>Messages: {sessionInfo.messages_count}</div>
        </div>
      )}
    </div>
  );
};

export default UserTestController;
