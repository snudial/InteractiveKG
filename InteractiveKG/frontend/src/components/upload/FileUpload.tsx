'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { GraphAPI } from '@/lib/api';
import { GraphData } from '@/types/graph';

interface FileUploadProps {
  onUploadSuccess: (data: GraphData) => void;
  onUploadError: (error: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    
    if (!file.name.endsWith('.json')) {
      setUploadStatus('error');
      setStatusMessage('请选择 JSON 格式的文件');
      onUploadError('请选择 JSON 格式的文件');
      return;
    }

    
    if (file.size > 10 * 1024 * 1024) {
      setUploadStatus('error');
      setStatusMessage('文件大小不能超过 10MB');
      onUploadError('文件大小不能超过 10MB');
      return;
    }

    setIsUploading(true);
    setUploadStatus('idle');
    setStatusMessage('正在上传文件...');

    try {
      const response = await GraphAPI.uploadJsonFile(file);
      
      if (response.error) {
        setUploadStatus('error');
        setStatusMessage(response.error);
        onUploadError(response.error);
      } else if (response.data) {
        setUploadStatus('success');
        setStatusMessage(`成功导入 ${response.data.nodes.length} 个节点和 ${response.data.relationships.length} 个关系`);
        onUploadSuccess(response.data);
      }
    } catch (error) {
      setUploadStatus('error');
      setStatusMessage('上传失败，请重试');
      onUploadError('上传失败，请重试');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
          transition-colors duration-200
          ${isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${isUploading ? 'pointer-events-none opacity-50' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <div className="flex flex-col items-center space-y-4">
          {isUploading ? (
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          ) : (
            <Upload className="h-12 w-12 text-gray-400" />
          )}
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isUploading ? '正在上传...' : '上传 JSON 文件'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              拖拽文件到此处或点击选择文件
            </p>
            <p className="text-xs text-gray-400 mt-1">
              支持 JSON 格式，最大 10MB
            </p>
          </div>
        </div>
      </div>

      {}
      {statusMessage && (
        <div className={`
          mt-4 p-3 rounded-md flex items-center space-x-2
          ${uploadStatus === 'success' 
            ? 'bg-green-50 text-green-800' 
            : uploadStatus === 'error'
            ? 'bg-red-50 text-red-800'
            : 'bg-blue-50 text-blue-800'
          }
        `}>
          {uploadStatus === 'success' && <CheckCircle className="h-5 w-5" />}
          {uploadStatus === 'error' && <AlertCircle className="h-5 w-5" />}
          {uploadStatus === 'idle' && <FileText className="h-5 w-5" />}
          <span className="text-sm">{statusMessage}</span>
        </div>
      )}
    </div>
  );
};
