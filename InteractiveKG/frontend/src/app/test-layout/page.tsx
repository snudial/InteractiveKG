'use client';

import React from 'react';
import { Settings, BarChart3 } from 'lucide-react';

export default function TestLayoutPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">布局测试页面</h1>
        
        {}
        <main className="flex gap-6 h-[calc(100vh-180px)]">
          {}
          <div className="w-80 flex flex-col space-y-4">
            {}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200/50 bg-gradient-to-r from-orange-50 to-red-50">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-gradient-to-r from-orange-400 to-red-500 rounded-lg flex items-center justify-center">
                    <BarChart3 className="h-4 w-4 text-white" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900">层级分析</h3>
                </div>
              </div>
              <div className="p-5">
                <div className="space-y-4">
                  <div className="bg-orange-50 p-3 rounded-md">
                    <p className="text-sm text-orange-800">
                      <strong>层级抽象功能</strong><br/>
                      • 多层级图谱分析<br/>
                      • 智能节点聚合<br/>
                      • 动态抽象级别调整<br/>
                      • 社区检测算法
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      抽象级别
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      defaultValue="3"
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>详细</span>
                      <span>抽象</span>
                    </div>
                  </div>
                  
                  <button className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700">
                    应用层级分析
                  </button>
                </div>
              </div>
            </div>

            {}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200/50 bg-gradient-to-r from-green-50 to-emerald-50">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-gradient-to-r from-green-400 to-emerald-500 rounded-lg flex items-center justify-center">
                    <Settings className="h-4 w-4 text-white" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900">知识推理</h3>
                </div>
              </div>
              <div className="p-5 max-h-96 always-show-scrollbar" style={{minHeight: '300px'}}>
                <div className="space-y-4">
                  <div className="bg-blue-50 p-3 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>智能问题求解与知识图谱更新</strong><br/>
                      • 多轮推理求解复杂问题<br/>
                      • 自动提取推理中的实体和关系<br/>
                      • 实时更新知识图谱数据库<br/>
                      • 与图可视化功能无缝联动
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      问题描述
                    </label>
                    <textarea
                      placeholder="请输入需要解决的复杂问题..."
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      rows={3}
                    />
                  </div>
                  
                  <button className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700">
                    开始智能求解
                  </button>
                  
                  {}
                  <div className="mt-6 space-y-4 max-h-64 always-show-scrollbar" style={{minHeight: '200px'}}>
                    <div className="border-t border-gray-200 pt-4">
                      <h3 className="text-lg font-medium text-gray-900 mb-3">🧠 智能求解结果</h3>

                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">📝 输入问题</h4>
                        <div className="bg-gray-50 p-3 rounded-md border text-sm">
                          <p className="text-gray-800">测试问题：验证布局是否正确</p>
                        </div>
                      </div>

                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">🎯 分析结果</h4>
                        <div className="p-3 rounded-md border h-48 always-show-scrollbar bg-green-50 border-green-200" style={{minHeight: '192px'}}>
                          <p className="text-sm text-green-800 mb-2">这是智能推理的结果。</p>
                          <p className="text-sm text-green-800 mb-2">外层容器滚动条：用于滚动整个知识推理模块</p>
                          <p className="text-sm text-green-800 mb-2">内层容器滚动条：用于滚动具体的推理结果</p>
                          <p className="text-sm text-green-800 mb-2">两个滚动条应该独立工作</p>
                          <p className="text-sm text-green-800 mb-2">第5行结果</p>
                          <p className="text-sm text-green-800 mb-2">第6行结果</p>
                          <p className="text-sm text-green-800 mb-2">第7行结果</p>
                          <p className="text-sm text-green-800 mb-2">第8行结果</p>
                          <p className="text-sm text-green-800 mb-2">第9行结果</p>
                          <p className="text-sm text-green-800 mb-2">第10行结果</p>
                          <p className="text-sm text-green-800 mb-2">第11行结果</p>
                          <p className="text-sm text-green-800 mb-2">第12行结果</p>
                          <p className="text-sm text-green-800 mb-2">第13行结果 - 需要滚动查看</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {}
          <div className="flex-1">
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 h-full overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200/50 bg-gradient-to-r from-slate-50 to-gray-50">
                <h2 className="text-lg font-semibold text-gray-900">知识图谱可视化</h2>
              </div>
              
              <div className="relative h-[calc(100%-80px)] flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <div className="text-6xl mb-4">🕸️</div>
                  <p className="text-lg">图谱可视化区域</p>
                  <p className="text-sm">这里显示知识图谱的可视化内容</p>
                </div>
              </div>
            </div>
          </div>

          {}
          <div className="w-80">
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 h-full overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200/50 bg-gradient-to-r from-blue-50 to-indigo-50">
                <h3 className="text-sm font-semibold text-gray-900">属性面板</h3>
              </div>
              
              <div className="p-5">
                <div className="text-center text-gray-500">
                  <div className="text-4xl mb-4">📊</div>
                  <p className="text-sm">选择节点或关系查看详细信息</p>
                </div>
              </div>
            </div>
          </div>
        </main>

        <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900 mb-2">布局测试结果</h3>
          <ul className="text-green-800 space-y-1">
            <li>• ✅ <strong>层级分析模块</strong>：应该正常显示，不被遮挡</li>
            <li>• ✅ <strong>知识推理模块</strong>：高度适中，有外层滚动条</li>
            <li>• ✅ <strong>结果显示区域</strong>：有内层滚动条，独立工作</li>
            <li>• ✅ <strong>整体布局</strong>：三栏布局，各模块不重叠</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
