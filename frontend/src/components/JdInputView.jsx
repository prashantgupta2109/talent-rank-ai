import React, { useState } from 'react';
import {
  FileText,
  Upload,
  Sparkles,
  Plus,
  X,
  Briefcase,
  CheckCircle2,
  ArrowRight,
  RotateCcw,
} from 'lucide-react';
import { parseJobDirect, createJob } from '../api/client';

const SAMPLE_DEFAULT_JD = `Job Title: Senior Python / Machine Learning Engineer

About Us:
We are developing next-generation AI platforms powering enterprise intelligence.

Responsibilities:
- Build and scale production-grade ML pipelines, NLP models, and LLM applications.
- Design high-performance REST APIs and microservices using Python and FastAPI.
- Implement Retrieval-Augmented Generation (RAG) architectures with vector search.
- Deploy models into containerized Kubernetes and AWS cloud environments with CI/CD.

Requirements:
- 4+ years of professional experience in Python and Machine Learning engineering.
- Strong hands-on expertise with PyTorch, scikit-learn, and Hugging Face Transformers.
- Proven experience building backend APIs with FastAPI, Flask, or Django.
- Solid understanding of SQL, PostgreSQL, and vector databases (ChromaDB or FAISS).
- Experience with Docker containerization and Git version control.
- Bachelor's or Master's degree in Computer Science or related STEM field.

Nice to Have:
- Experience with Sentence Transformers, spaCy, and Large Language Models (LLMs).
- Knowledge of Kubernetes, AWS (EC2, S3), and CI/CD pipelines (GitHub Actions).`;

export default function JdInputView({ onJobCreated, currentJob }) {
  const [jdText, setJdText] = useState(SAMPLE_DEFAULT_JD);
  const [jobTitle, setJobTitle] = useState('Senior Python / Machine Learning Engineer');
  const [parsing, setParsing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [parsedData, setParsedData] = useState(null);
  const [newRequiredSkill, setNewRequiredSkill] = useState('');
  const [newPreferredSkill, setNewPreferredSkill] = useState('');
  const [error, setError] = useState(null);

  // Parse text to preview skills chips
  const handleParsePreview = async () => {
    if (!jdText.trim()) {
      setError('Please enter or upload a Job Description first.');
      return;
    }
    setError(null);
    setParsing(true);
    try {
      const data = await parseJobDirect(jdText);
      setParsedData(data);
      if (data.title) setJobTitle(data.title);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to parse Job Description');
    } finally {
      setParsing(false);
    }
  };

  // Add skill chip
  const addSkill = (type) => {
    if (type === 'required' && newRequiredSkill.trim()) {
      setParsedData((prev) => ({
        ...prev,
        required_skills: [...(prev?.required_skills || []), newRequiredSkill.trim()],
      }));
      setNewRequiredSkill('');
    } else if (type === 'preferred' && newPreferredSkill.trim()) {
      setParsedData((prev) => ({
        ...prev,
        preferred_skills: [...(prev?.preferred_skills || []), newPreferredSkill.trim()],
      }));
      setNewPreferredSkill('');
    }
  };

  // Remove skill chip
  const removeSkill = (type, index) => {
    setParsedData((prev) => {
      const list = type === 'required' ? [...prev.required_skills] : [...prev.preferred_skills];
      list.splice(index, 1);
      return type === 'required'
        ? { ...prev, required_skills: list }
        : { ...prev, preferred_skills: list };
    });
  };

  // Save parsed JD to backend database
  const handleSaveAndProceed = async () => {
    if (!jdText.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await createJob(jdText, jobTitle);
      // Merge any user edits made to skills/years in the preview
      if (parsedData) {
        saved.required_skills = parsedData.required_skills;
        saved.preferred_skills = parsedData.preferred_skills;
        saved.min_years_experience = parsedData.min_years_experience;
      }
      onJobCreated(saved);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to save job description');
    } finally {
      setSaving(false);
    }
  };

  // File upload reader
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setJdText(event.target?.result || '');
      setParsedData(null);
    };
    reader.readAsText(file);
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center">
            <Briefcase className="w-5 h-5 mr-2 text-blue-600" />
            Module 1: Job Description Input
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Paste or upload a Job Description to extract requirements, skills, experience, and criteria.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              setJdText(SAMPLE_DEFAULT_JD);
              setParsedData(null);
            }}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 flex items-center transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1 text-slate-500" />
            Load Sample JD
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
          {error}
        </div>
      )}

      {/* Input Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Textarea & File Upload */}
        <div className="space-y-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Raw Job Description Text
            </label>
            <label className="cursor-pointer text-xs font-medium text-blue-600 hover:text-blue-800 flex items-center">
              <Upload className="w-3.5 h-3.5 mr-1" />
              Upload text file
              <input type="file" accept=".txt,.md" className="hidden" onChange={handleFileUpload} />
            </label>
          </div>

          <textarea
            value={jdText}
            onChange={(e) => {
              setJdText(e.target.value);
              setParsedData(null);
            }}
            rows={14}
            placeholder="Paste complete Job Description here..."
            className="w-full text-xs font-mono p-3 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-800 resize-none flex-1 leading-relaxed"
          />

          <div className="flex justify-between items-center pt-2">
            <span className="text-[11px] text-slate-500">
              {jdText.split(/\s+/).filter(Boolean).length} words
            </span>
            <button
              onClick={handleParsePreview}
              disabled={parsing || !jdText.trim()}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white flex items-center shadow-sm disabled:opacity-50 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              {parsing ? 'Extracting Criteria...' : 'Extract & Preview Skills'}
            </button>
          </div>
        </div>

        {/* Right Column: Editable Chips Preview */}
        <div className="space-y-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Extracted Criteria &amp; Skill Chips
            </label>
            {parsedData && (
              <span className="text-[11px] font-semibold text-emerald-600 flex items-center">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                Parsed Deterministically
              </span>
            )}
          </div>

          {parsedData ? (
            <div className="space-y-5 flex-1 overflow-y-auto pr-1">
              {/* Job Title */}
              <div>
                <label className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">
                  Target Job Title
                </label>
                <input
                  type="text"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full text-xs font-semibold p-2 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Experience and Education Quick Stat */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">
                    Min Experience
                  </span>
                  <div className="flex items-center space-x-1 mt-1">
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      value={parsedData.min_years_experience}
                      onChange={(e) =>
                        setParsedData({
                          ...parsedData,
                          min_years_experience: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-16 text-sm font-bold p-1 bg-white border border-slate-200 rounded"
                    />
                    <span className="text-xs text-slate-600 font-medium">years</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">
                    Education Detected
                  </span>
                  <div className="text-xs font-semibold text-slate-700 mt-1 truncate">
                    {parsedData.education_requirements?.join(', ') || 'Degree not specified'}
                  </div>
                </div>
              </div>

              {/* Required Skills Editable Chips */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 flex items-center">
                    <span className="w-2 h-2 rounded-full bg-blue-600 mr-1.5" />
                    Required Skills ({parsedData.required_skills?.length || 0})
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">Weight: 1.0</span>
                </div>
                <div className="flex flex-wrap gap-1.5 p-2 bg-slate-50 rounded-lg border border-slate-100 min-h-[50px]">
                  {parsedData.required_skills?.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200 group"
                    >
                      {skill}
                      <button
                        onClick={() => removeSkill('required', idx)}
                        className="ml-1 text-blue-500 hover:text-blue-900 focus:outline-none"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex space-x-1.5">
                  <input
                    type="text"
                    value={newRequiredSkill}
                    onChange={(e) => setNewRequiredSkill(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addSkill('required')}
                    placeholder="Add required skill (press Enter)..."
                    className="flex-1 text-xs p-1.5 rounded border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => addSkill('required')}
                    className="px-2.5 py-1 text-xs font-medium rounded bg-slate-100 hover:bg-slate-200 text-slate-700"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Preferred Skills Editable Chips */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 flex items-center">
                    <span className="w-2 h-2 rounded-full bg-teal-500 mr-1.5" />
                    Preferred / Nice to Have ({parsedData.preferred_skills?.length || 0})
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">Weight: 0.5</span>
                </div>
                <div className="flex flex-wrap gap-1.5 p-2 bg-slate-50 rounded-lg border border-slate-100 min-h-[50px]">
                  {parsedData.preferred_skills?.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-teal-100 text-teal-800 border border-teal-200"
                    >
                      {skill}
                      <button
                        onClick={() => removeSkill('preferred', idx)}
                        className="ml-1 text-teal-500 hover:text-teal-900 focus:outline-none"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  {!parsedData.preferred_skills?.length && (
                    <span className="text-xs text-slate-500 italic p-1">No preferred skills</span>
                  )}
                </div>
                <div className="flex space-x-1.5">
                  <input
                    type="text"
                    value={newPreferredSkill}
                    onChange={(e) => setNewPreferredSkill(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addSkill('preferred')}
                    placeholder="Add preferred skill..."
                    className="flex-1 text-xs p-1.5 rounded border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                  <button
                    onClick={() => addSkill('preferred')}
                    className="px-2.5 py-1 text-xs font-medium rounded bg-slate-100 hover:bg-slate-200 text-slate-700"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500 border border-dashed border-slate-200 rounded-lg">
              <Sparkles className="w-8 h-8 text-slate-300 mb-2" />
              <p className="text-xs font-medium">No extracted criteria yet</p>
              <p className="text-[11px] text-slate-500 max-w-xs mt-1">
                Click "Extract &amp; Preview Skills" to automatically identify required skills, preferred qualifications, and experience.
              </p>
            </div>
          )}

          {/* Action Footer */}
          <div className="pt-3 border-t border-slate-100 flex justify-end">
            <button
              onClick={handleSaveAndProceed}
              disabled={saving || !jdText.trim()}
              className="px-5 py-2.5 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white flex items-center shadow-md disabled:opacity-50 transition-colors"
            >
              <span>{saving ? 'Saving Job...' : 'Confirm Job & Proceed to Resumes'}</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
