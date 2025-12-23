import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { ScrollArea } from './scroll-area';
import { CheckCircle, Clock, AlertCircle, Brain, Database } from 'lucide-react';

interface KGOTResult {
  success: boolean;
  answer: string;
  execution_time: number;
  iterations: number;
  kg_updates: number;
  error?: string;
  reasoning_steps: string[];
}

interface KGOTResultViewProps {
  problem: string;
  result: KGOTResult | null;
  isVisible: boolean;
  onClose?: () => void;
}

export const KGOTResultView: React.FC<KGOTResultViewProps> = ({
  problem,
  result,
  isVisible,
  onClose
}) => {
  if (!isVisible || !result) {
    return null;
  }

  const getStatusIcon = () => {
    if (result.success) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    } else {
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusColor = () => {
    return result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';
  };

  return (
    <div className="fixed top-4 left-4 right-4 z-50 max-w-4xl mx-auto">
      <Card className={`shadow-lg ${getStatusColor()}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <CardTitle className="text-lg">
                {result.success ? 'Intelligent Solving Complete' : 'Solving Failed'}
              </CardTitle>
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold"
              >
                ×
              </button>
            )}
          </div>
          
          {}
          <div className="flex gap-4 mt-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {result.execution_time.toFixed(2)}s
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Brain className="h-3 w-3" />
              {result.iterations} Reasoning Rounds
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Database className="h-3 w-3" />
              {result.kg_updates} Knowledge Updates
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {}
          <div>
            <h4 className="font-medium text-gray-700 mb-2">📝 Input Question</h4>
            <div className="bg-gray-50 p-3 rounded-md border">
              <p className="text-gray-800">{problem}</p>
            </div>
          </div>

          {}
          <div>
            <h4 className="font-medium text-gray-700 mb-2">
              {result.success ? '🎯 Solving Results' : '❌ Error Information'}
            </h4>
            <ScrollArea className="h-32">
              <div className={`p-3 rounded-md border ${
                result.success
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className={`prose prose-sm max-w-none ${
                  result.success
                    ? 'prose-headings:text-green-900 prose-strong:text-green-900 prose-p:text-green-800 prose-li:text-green-800'
                    : 'prose-headings:text-red-900 prose-strong:text-red-900 prose-p:text-red-800 prose-li:text-red-800'
                }`}>
                  <ReactMarkdown>{result.success ? result.answer : result.error || ''}</ReactMarkdown>
                </div>
              </div>
            </ScrollArea>
          </div>

          {}
          {result.reasoning_steps && result.reasoning_steps.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-700 mb-2">🧠 Complete Reasoning Process</h4>
              <ScrollArea className="h-40">
                <div className="space-y-3">
                  {result.reasoning_steps.map((step, index) => {
                    
                    const sections = step.split('###').filter(s => s.trim());

                    return (
                      <div key={index} className="bg-blue-50 p-3 rounded border-l-4 border-blue-200">
                        <div className="font-medium text-blue-900 mb-2">
                          Round {index + 1} Reasoning
                        </div>

                        {sections.map((section, sectionIndex) => {
                          const lines = section.trim().split('\n');
                          const title = lines[0];
                          const content = lines.slice(1).join('\n').trim();

                          if (!content) return null;

                          return (
                            <div key={sectionIndex} className="mb-2">
                              <div className="text-xs font-medium text-blue-700 mb-1">
                                {title}
                              </div>
                              <div className="text-xs text-blue-800 bg-white bg-opacity-50 p-2 rounded">
                                {content}
                              </div>
                            </div>
                          );
                        })}

                        {sections.length === 0 && (
                          <p className="text-sm text-blue-800">{step}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </div>
          )}

          {}
          {result.success && result.kg_updates > 0 && (
            <div className="bg-blue-50 p-3 rounded-md border border-blue-200">
              <p className="text-blue-800 text-sm">
                ✅ Knowledge graph successfully updated with {result.kg_updates} new knowledge elements.
                You can view the new nodes and relationships in the graph visualization interface.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
