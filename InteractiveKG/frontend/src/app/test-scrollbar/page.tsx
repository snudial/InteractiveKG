'use client';

import React from 'react';

export default function TestScrollbarPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">滚动条测试页面</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">测试1: 内容较少 - 滚动条应该始终显示</h2>
            <div className="h-64 always-show-scrollbar bg-gray-50 p-4 rounded border">
              <p className="text-gray-700">这是一个内容较少的容器。</p>
              <p className="text-gray-700">滚动条应该始终显示，即使内容没有溢出。</p>
              <p className="text-gray-700">这样用户就能知道这个区域是可滚动的。</p>
            </div>
          </div>

          {}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">测试2: 内容较多 - 滚动条应该正常工作</h2>
            <div className="h-64 always-show-scrollbar bg-gray-50 p-4 rounded border">
              <p className="text-gray-700 mb-2">这是一个内容较多的容器。</p>
              <p className="text-gray-700 mb-2">内容会超出容器高度。</p>
              <p className="text-gray-700 mb-2">滚动条应该正常工作。</p>
              <p className="text-gray-700 mb-2">第5行内容</p>
              <p className="text-gray-700 mb-2">第6行内容</p>
              <p className="text-gray-700 mb-2">第7行内容</p>
              <p className="text-gray-700 mb-2">第8行内容</p>
              <p className="text-gray-700 mb-2">第9行内容</p>
              <p className="text-gray-700 mb-2">第10行内容</p>
              <p className="text-gray-700 mb-2">第11行内容</p>
              <p className="text-gray-700 mb-2">第12行内容</p>
              <p className="text-gray-700 mb-2">第13行内容</p>
              <p className="text-gray-700 mb-2">第14行内容</p>
              <p className="text-gray-700 mb-2">第15行内容</p>
              <p className="text-gray-700 mb-2">第16行内容</p>
              <p className="text-gray-700 mb-2">第17行内容</p>
              <p className="text-gray-700 mb-2">第18行内容</p>
              <p className="text-gray-700 mb-2">第19行内容</p>
              <p className="text-gray-700 mb-2">第20行内容 - 这里应该需要滚动才能看到</p>
            </div>
          </div>

          {}
          <div className="bg-white rounded-lg shadow-lg p-6 md:col-span-2">
            <h2 className="text-xl font-semibold mb-4">测试3: 模拟知识推理模块的双滚动条结构</h2>

            {}
            <div className="flex-1 bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 flex flex-col">
              <div className="px-5 py-4 border-b border-gray-200/50 bg-gradient-to-r from-green-50 to-emerald-50 flex-shrink-0">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 bg-gradient-to-r from-green-400 to-emerald-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-xs">🧠</span>
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900">知识推理</h3>
                </div>
              </div>

              {}
              <div className="flex-1 always-show-scrollbar" style={{minHeight: '600px', maxHeight: '600px'}}>
                <div className="p-4" style={{minHeight: '800px'}}>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">🧠 增强KGOT智能助手</h3>

                  {}
                  <div className="bg-blue-50 p-3 rounded-md mb-4">
                    <p className="text-sm text-blue-800">
                      <strong>功能1：智能问题求解与知识图谱更新</strong><br/>
                      • 多轮推理求解复杂问题<br/>
                      • 自动提取推理中的实体和关系<br/>
                      • 实时更新知识图谱数据库<br/>
                      • 与图可视化功能无缝联动
                    </p>
                  </div>

                  {}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      问题描述
                    </label>
                    <textarea
                      placeholder="请输入需要解决的复杂问题，系统将进行多轮推理并自动更新知识图谱..."
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      rows={4}
                      defaultValue="这是一个测试问题，用来验证双滚动条功能。"
                    />
                  </div>

                  {}
                  <button className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 mb-6">
                    开始智能求解
                  </button>

                  {}
                  <div className="mt-6 space-y-4 h-96 always-show-scrollbar" style={{minHeight: '384px'}}>
                    <div className="border-t border-gray-200 pt-4">
                      <h3 className="text-lg font-medium text-gray-900 mb-3">🧠 智能求解结果</h3>

                      {}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">📝 输入问题</h4>
                        <div className="bg-gray-50 p-3 rounded-md border text-sm">
                          <p className="text-gray-800">这是一个测试问题，用来验证双滚动条功能。</p>
                        </div>
                      </div>

                      {}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">🎯 分析结果</h4>
                        <div className="p-3 rounded-md border h-80 always-show-scrollbar bg-green-50 border-green-200" style={{minHeight: '320px'}}>
                          <p className="text-sm text-green-800 mb-2">这是智能推理的结果。</p>
                          <p className="text-sm text-green-800 mb-2">这个区域有自己的滚动条（第二个滚动条）。</p>
                          <p className="text-sm text-green-800 mb-2">外层容器也有滚动条（第一个滚动条）。</p>
                          <p className="text-sm text-green-800 mb-2">两个滚动条应该独立工作。</p>
                          <p className="text-sm text-green-800 mb-2">第5行结果</p>
                          <p className="text-sm text-green-800 mb-2">第6行结果</p>
                          <p className="text-sm text-green-800 mb-2">第7行结果</p>
                          <p className="text-sm text-green-800 mb-2">第8行结果</p>
                          <p className="text-sm text-green-800 mb-2">第9行结果</p>
                          <p className="text-sm text-green-800 mb-2">第10行结果</p>
                          <p className="text-sm text-green-800 mb-2">第11行结果</p>
                          <p className="text-sm text-green-800 mb-2">第12行结果</p>
                          <p className="text-sm text-green-800 mb-2">第13行结果</p>
                          <p className="text-sm text-green-800 mb-2">第14行结果</p>
                          <p className="text-sm text-green-800 mb-2">第15行结果</p>
                          <p className="text-sm text-green-800 mb-2">第16行结果</p>
                          <p className="text-sm text-green-800 mb-2">第17行结果</p>
                          <p className="text-sm text-green-800 mb-2">第18行结果</p>
                          <p className="text-sm text-green-800 mb-2">第19行结果</p>
                          <p className="text-sm text-green-800 mb-2">第20行结果 - 需要滚动查看</p>
                        </div>
                      </div>

                      {}
                      <div className="flex flex-wrap gap-2 text-xs">
                        <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                          ⏱️ 2.34s
                        </span>
                        <span className="inline-flex items-center px-2 py-1 rounded-full bg-purple-100 text-purple-800">
                          🧠 3 轮推理
                        </span>
                        <span className="inline-flex items-center px-2 py-1 rounded-full bg-green-100 text-green-800">
                          📊 5 知识更新
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">双滚动条测试说明</h3>
          <ul className="text-blue-800 space-y-1">
            <li>• <strong>测试1和2</strong>：基础滚动条测试，验证单个容器的滚动条显示</li>
            <li>• <strong>测试3</strong>：双滚动条测试，模拟知识推理模块的实际结构</li>
            <li>• <strong>外层滚动条</strong>：用于滚动整个模块内容（标题、输入框、结果等）</li>
            <li>• <strong>内层滚动条</strong>：用于滚动具体的推理结果内容</li>
            <li>• <strong>预期效果</strong>：两个滚动条都应该始终可见，独立工作，互不干扰</li>
            <li>• <strong>样式要求</strong>：滚动条应该美观，与界面风格一致</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
