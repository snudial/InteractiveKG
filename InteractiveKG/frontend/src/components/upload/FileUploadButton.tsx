'use client';

import React, { useRef, useState } from 'react';
import { Upload, Loader2 } from 'lucide-react';
import { GraphAPI } from '@/lib/api';

interface FileUploadButtonProps {
  onUploadSuccess: (data: any) => void;
  onUploadError: (error: string) => void;
}

export const FileUploadButton: React.FC<FileUploadButtonProps> = ({
  onUploadSuccess,
  onUploadError
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    
    if (!file.name.endsWith('.json')) {
      onUploadError('Please select a JSON format file');
      return;
    }

    
    if (file.size > 10 * 1024 * 1024) {
      onUploadError('File size cannot exceed 10MB');
      return;
    }

    setIsUploading(true);

    try {
      const response = await GraphAPI.uploadJsonFile(file);
      
      if (response.error) {
        onUploadError(response.error);
      } else if (response.data) {
        onUploadSuccess(response.data);
      }
    } catch (error) {
      onUploadError('Upload failed, please try again');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileSelect}
        className="hidden"
      />
      <button
        onClick={handleClick}
        disabled={isUploading}
        className="inline-flex items-center px-3 py-2 border border-blue-300 shadow-sm text-sm leading-4 font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Uploading...
          </>
        ) : (
          <>
            <Upload className="h-4 w-4 mr-2" />
            Data Upload
          </>
        )}
      </button>
    </>
  );
};
