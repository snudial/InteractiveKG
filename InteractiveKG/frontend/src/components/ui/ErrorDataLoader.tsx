'use client';

import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Database, 
  Loader2,
  CheckCircle,
  Info,
  Eye,
  Zap
} from 'lucide-react';
import '@/styles/scrollbar.css';

interface ErrorDataSet {
  id: string;
  name: string;
  description: string;
  errorTypes: string[];
  nodeCount: number;
  errorNodeCount: number;
}

interface ErrorDataLoaderProps {
  onLoadErrorData: (datasetId: string) => Promise<void>;
  isLoading?: boolean;
  currentDataset?: string | null;
  modalMode?: boolean;
}

const ErrorDataLoader: React.FC<ErrorDataLoaderProps> = ({
  onLoadErrorData,
  isLoading = false,
  currentDataset = null,
  modalMode = false
}) => {
  const [selectedDataset, setSelectedDataset] = useState<string>('quantum_computing_errors');

  
  const errorDataSets: ErrorDataSet[] = [
    {
      id: 'quantum_computing_errors',
      name: 'Quantum Computing Applications (with AI Hallucinations)',
      description: 'Contains quantum computing related knowledge, but mixed with AI hallucination nodes like "time travel"',
      errorTypes: ['Concept Hallucinations', 'Non-existent Applications', 'Science Fiction Concepts'],
      nodeCount: 25,
      errorNodeCount: 3
    },
    {
      id: 'medical_research_errors',
      name: 'Medical Research (with Incorrect Associations)',
      description: 'Medical research data containing incorrect drug associations and false treatment methods',
      errorTypes: ['Incorrect Associations', 'False Treatments', 'Outdated Information'],
      nodeCount: 30,
      errorNodeCount: 4
    },
    {
      id: 'financial_analysis_errors',
      name: 'Financial Analysis (with Outdated Data)',
      description: 'Financial market analysis containing outdated company information and incorrect market relationships',
      errorTypes: ['Outdated Data', 'Incorrect Relationships', 'Fake Companies'],
      nodeCount: 20,
      errorNodeCount: 2
    }
  ];

  const handleLoadData = async () => {
    if (selectedDataset) {
      await onLoadErrorData(selectedDataset);
    }
  };

  const selectedDatasetInfo = errorDataSets.find(ds => ds.id === selectedDataset);

  return (
    <div
      id="error-data-loader"
      className="bg-white rounded-lg shadow p-4 max-h-72 overflow-y-auto error-loader-scrollbar smooth-scroll"
    >
      <div className="flex items-center space-x-2 mb-4">
        <AlertTriangle className="h-5 w-5 text-orange-600" />
        <h3 className="text-lg font-medium text-gray-900">错误数据加载器</h3>
      </div>

      <div className="mb-4 p-3 bg-orange-50 rounded-md">
        <div className="flex items-start space-x-2">
          <Info className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-orange-800">
            <p className="font-medium mb-1">第二阶段：修正AI错误</p>
            <p>为了模拟真实场景，我们将加载包含AI"幻觉"的知识图谱。这些错误混杂在正确信息中，需要您仔细识别和修正。</p>
          </div>
        </div>
      </div>

      {}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          选择错误数据集
        </label>
        <div className="space-y-2 max-h-40 overflow-y-auto dataset-selection-scrollbar smooth-scroll">
          {errorDataSets.map((dataset) => {
            const isSelected = selectedDataset === dataset.id;
            const isCurrentlyLoaded = currentDataset === dataset.id;
            
            return (
              <div
                key={dataset.id}
                className={`p-3 rounded-md border cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-blue-50 border-blue-200'
                    : 'bg-white border-gray-200 hover:bg-gray-50'
                } ${isCurrentlyLoaded ? 'ring-2 ring-green-200' : ''}`}
                onClick={() => setSelectedDataset(dataset.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <input
                        type="radio"
                        checked={isSelected}
                        onChange={() => setSelectedDataset(dataset.id)}
                        className="text-blue-600"
                      />
                      <h4 className="text-sm font-medium text-gray-900">
                        {dataset.name}
                      </h4>
                      {isCurrentlyLoaded && (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1 ml-6">
                      {dataset.description}
                    </p>
                    
                    {}
                    <div className="flex items-center space-x-4 mt-2 ml-6 text-xs text-gray-500">
                      <span className="flex items-center space-x-1">
                        <Database className="h-3 w-3" />
                        <span>{dataset.nodeCount} 节点</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <AlertTriangle className="h-3 w-3 text-orange-500" />
                        <span>{dataset.errorNodeCount} 错误</span>
                      </span>
                    </div>
                    
                    {}
                    <div className="flex flex-wrap gap-1 mt-2 ml-6">
                      {dataset.errorTypes.map((errorType, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded"
                        >
                          {errorType}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {}
      {selectedDatasetInfo && (
        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
            <Eye className="h-4 w-4 mr-1" />
            数据集预览
          </h4>
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>总节点数:</strong> {selectedDatasetInfo.nodeCount}</p>
            <p><strong>错误节点数:</strong> {selectedDatasetInfo.errorNodeCount}</p>
            <p><strong>错误率:</strong> {Math.round((selectedDatasetInfo.errorNodeCount / selectedDatasetInfo.nodeCount) * 100)}%</p>
          </div>
        </div>
      )}

      {}
      <button
        onClick={handleLoadData}
        disabled={isLoading || !selectedDataset}
        className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
        ) : (
          <Zap className="h-4 w-4 mr-2" />
        )}
        {isLoading ? '加载中...' : '加载错误数据集'}
      </button>

      {}
      {currentDataset && (
        <div className="mt-4 p-3 bg-green-50 rounded-md">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">
              已加载数据集
            </span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            {errorDataSets.find(ds => ds.id === currentDataset)?.name || currentDataset}
          </p>
        </div>
      )}

      {}
      <div className="mt-4 p-3 bg-blue-50 rounded-md">
        <div className="flex items-start space-x-2">
          <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">使用提示</p>
            <ul className="text-xs space-y-1">
              <li>• 加载后，使用层级抽象功能观察数据分布</li>
              <li>• 寻找格格不入的节点或异常分组</li>
              <li>• 使用"为什么？"功能分析可疑节点</li>
              <li>• 通过CRUD操作修正或删除错误数据</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorDataLoader;
