import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileCheck,
  FileText,
  AlertCircle,
  CheckCircle2,
  Trash2,
  Sparkles,
  ArrowRight,
  FolderOpen,
} from 'lucide-react';
import { uploadJobResumes, triggerJobMatch } from '../api/client';

export default function ResumeUploadView({ currentJob, onUploadComplete, onMatchingComplete }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles) => {
    const valid = newFiles.filter((f) => {
      const ext = f.name.toLowerCase();
      return ext.endsWith('.pdf') || ext.endsWith('.docx') || ext.endsWith('.doc');
    });

    if (valid.length < newFiles.length) {
      setError('Some files were ignored because only PDF and DOCX formats are supported.');
    } else {
      setError(null);
    }

    setSelectedFiles((prev) => {
      const existingNames = new Set(prev.map((p) => p.name));
      const filtered = valid.filter((f) => !existingNames.has(f.name));
      return [...prev, ...filtered];
    });
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Upload the selected batch
  const handleUploadBatch = async () => {
    if (!currentJob?.id) {
      setError('No active Job Description selected.');
      return;
    }
    if (selectedFiles.length === 0) {
      setError('Please select or drag at least 1 resume file.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const result = await uploadJobResumes(
        currentJob.id,
        selectedFiles,
        (progressEvent) => {
          const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(pct);
        }
      );
      setUploadResult(result);
      if (onUploadComplete) onUploadComplete(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Batch upload failed');
    } finally {
      setUploading(false);
    }
  };

  // Trigger matching and proceed to ranking
  const handleRunMatching = async () => {
    if (!currentJob?.id) return;
    setMatching(true);
    setError(null);
    try {
      const matchData = await triggerJobMatch(currentJob.id);
      if (onMatchingComplete) onMatchingComplete(matchData);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Matching calculation failed');
    } finally {
      setMatching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center">
            <UploadCloud className="w-5 h-5 mr-2 text-blue-600" />
            Module 2: Batch Resume Upload
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Active Job: <span className="font-semibold text-slate-800">{currentJob?.title || 'Job #1'}</span>. Upload candidate resumes (supports 10+ batch PDF &amp; DOCX files).
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-300 hover:border-blue-500 bg-white hover:bg-blue-50/20 rounded-xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-3"
      >
        <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
          <UploadCloud className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-800">
            Drag and drop resume files here, or <span className="text-blue-600 underline">browse</span>
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Supports batch upload of 10+ resumes (PDF and DOCX formats up to 15MB each)
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-slate-700">
                Selected Resumes ({selectedFiles.length})
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-semibold">
                Ready to Process
              </span>
            </div>
            <button
              onClick={() => setSelectedFiles([])}
              className="text-xs text-rose-600 hover:text-rose-800 flex items-center"
            >
              <Trash2 className="w-3.5 h-3.5 mr-1" />
              Clear all
            </button>
          </div>

          <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
            {selectedFiles.map((file, idx) => {
              const isPdf = file.name.toLowerCase().endsWith('.pdf');
              return (
                <div key={idx} className="p-3 px-4 flex items-center justify-between text-xs hover:bg-slate-50">
                  <div className="flex items-center space-x-3">
                    <span className={`p-1.5 rounded ${isPdf ? 'bg-rose-100 text-rose-600' : 'bg-blue-100 text-blue-600'}`}>
                      <FileText className="w-4 h-4" />
                    </span>
                    <div>
                      <p className="font-semibold text-slate-800">{file.name}</p>
                      <p className="text-[10px] text-slate-500">
                        {(file.size / 1024).toFixed(1)} KB • {isPdf ? 'PDF Document' : 'Word Document'}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(idx);
                    }}
                    className="p-1 rounded text-slate-500 hover:text-rose-600 hover:bg-slate-100"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Upload Progress Bar */}
          {uploading && (
            <div className="p-4 border-t border-slate-100 bg-blue-50/50 space-y-1">
              <div className="flex justify-between text-xs font-semibold text-blue-900">
                <span>Uploading and extracting batch concurrently...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-blue-200 overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Action Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              {uploadResult
                ? `Uploaded ${uploadResult.total_successful} candidate resumes successfully.`
                : `${selectedFiles.length} files queued.`}
            </span>

            <div className="flex items-center space-x-3">
              {!uploadResult ? (
                <button
                  onClick={handleUploadBatch}
                  disabled={uploading}
                  className="px-4 py-2 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm disabled:opacity-50 flex items-center transition-colors"
                >
                  <FileCheck className="w-3.5 h-3.5 mr-1.5" />
                  {uploading ? 'Processing Batch...' : `Upload ${selectedFiles.length} Resumes`}
                </button>
              ) : (
                <button
                  onClick={handleRunMatching}
                  disabled={matching}
                  className="px-5 py-2 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-md flex items-center transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                  {matching ? 'Calculating AI Matches...' : 'Run AI Matching & View Rankings'}
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
